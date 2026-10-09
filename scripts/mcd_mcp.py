#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦当劳中国 MCP 零依赖客户端（Streamable HTTP / JSON-RPC 2.0）。

仅用 Python 标准库，Windows / macOS / Linux 通用。
前置：设置环境变量 MCD_MCP_TOKEN（https://open.mcd.cn/mcp 申请），可选 MCD_MCP_URL。
无 Token 也能体验：加 --demo（或设 MCD_DEMO=1）走内置真实感 Mock 数据，全流程可演示。

用法：
  python mcd_mcp.py init                            # 初始化并验证 Token
  python mcd_mcp.py list                            # 列出全部工具及参数
  python mcd_mcp.py call <tool> [--args '<json>']   # 调用工具
  python mcd_mcp.py save --budget 30 [--city 上海]  # ★省钱最优解引擎
  python mcd_mcp.py demo                            # 打印一段完整演示对话

任何命令后加 --demo 即可离线运行（如 python mcd_mcp.py save --budget 30 --demo）。
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

DEFAULT_URL = "https://mcp.mcd.cn"
PROTOCOL = "2025-06-18"

# ---------------------------------------------------------------------------
# 内置 Mock 数据（仅 --demo 模式使用，用于无 Token 演示，非真实数据）
# ---------------------------------------------------------------------------
MOCK_MENU = [
    {"name": "麦辣鸡腿堡", "cat": "主食", "price": 21.5, "cal": 517},
    {"name": "板烧鸡腿堡", "cat": "主食", "price": 24.0, "cal": 502},
    {"name": "双层吉士汉堡", "cat": "主食", "price": 22.0, "cal": 460},
    {"name": "麦香鸡", "cat": "主食", "price": 14.0, "cal": 410},
    {"name": "招财牛堡", "cat": "主食", "price": 25.0, "cal": 560},
    {"name": "中薯条", "cat": "小食", "price": 12.0, "cal": 320},
    {"name": "麦辣鸡翅(2块)", "cat": "小食", "price": 11.0, "cal": 290},
    {"name": "玉米杯", "cat": "小食", "price": 9.0, "cal": 130},
    {"name": "中可乐", "cat": "饮料", "price": 9.0, "cal": 150},
    {"name": "雪碧", "cat": "饮料", "price": 9.0, "cal": 150},
    {"name": "美禄", "cat": "饮料", "price": 11.0, "cal": 200},
    {"name": "红茶", "cat": "饮料", "price": 8.0, "cal": 5},
    {"name": "圆筒冰淇淋", "cat": "甜品", "price": 5.0, "cal": 180},
    {"name": "苹果派", "cat": "甜品", "price": 7.0, "cal": 240},
    {"name": "麦旋风", "cat": "甜品", "price": 12.0, "cal": 350},
]

MOCK_COUPONS = [
    {"id": "c1", "name": "满40减8元", "type": "fullreduce", "threshold": 40, "off": 8},
    {"id": "c2", "name": "指定汉堡买一送一", "type": "bogo", "target": "汉堡"},
    {"id": "c3", "name": "中薯条立减3元", "type": "itemoff", "target": "薯条", "off": 3},
    {"id": "c4", "name": "甜品第二件半价", "type": "half2", "target": "甜品"},
]


def _err(msg):
    print(msg, file=sys.stderr)


class McdMcp:
    def __init__(self, url=None, token=None, demo=False):
        self.url = (url or os.environ.get("MCD_MCP_URL") or DEFAULT_URL).rstrip("/")
        self.token = token if token is not None else os.environ.get("MCD_MCP_TOKEN")
        self.session_id = None
        self.demo = demo

    # ------------------------- 真实 HTTP 层 -------------------------
    def _post(self, payload, extra_headers=None):
        if self.demo:
            return self._demo_reply(payload)
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "mcd-mcp-client/1.1",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if extra_headers:
            headers.update(extra_headers)

        req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (401, 403):
                raise SystemExit(
                    "❌ %d：Token 缺失/未被接受（未鉴权请求会被网关拒绝）。请到 https://open.mcd.cn/mcp 登录获取并写入 MCD_MCP_TOKEN；"
                    "或加 --demo 体验离线演示。" % e.code
                )
            if e.code == 429:
                raise SystemExit("❌ 429：触发限流（每 Token 每分钟 600 次），请稍后重试")
            raise SystemExit("❌ HTTP %d: %s" % (e.code, body[:300]))
        except Exception as e:  # 网络/超时等
            raise SystemExit("❌ 网络错误：%s。请检查网络后重试。" % (type(e).__name__,))

        sid = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid

        ct = resp.headers.get("Content-Type", "")
        raw = resp.read().decode("utf-8", "replace")
        if "text/event-stream" in ct:
            return self._parse_sse(raw)
        if not raw.strip():
            return None
        return json.loads(raw)

    @staticmethod
    def _parse_sse(raw):
        data_parts = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                data_parts.append(line[len("data:"):].strip())
        if not data_parts:
            return None
        return json.loads(data_parts[-1])

    # ------------------------- Demo 层 -------------------------
    def _demo_reply(self, payload):
        method = payload.get("method", "")
        mid = payload.get("id")
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL, "capabilities": {},
                "serverInfo": {"name": "mcd-mcp-mock", "version": "demo-1.0"}}}
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": mid, "result": {"tools": MOCK_TOOLS}}
        if method == "tools/call":
            name = payload["params"]["name"]
            args = payload["params"].get("arguments", {}) or {}
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": json.dumps(
                    self._demo_tool(name, args), ensure_ascii=False)}]}}
        return {"jsonrpc": "2.0", "id": mid, "result": {}}

    @staticmethod
    def _demo_tool(name, args):
        if name in ("now-time-info",):
            return {"time": "2026-10-09 19:30", "period": "晚餐"}
        if name in ("available-coupons", "my-coupons"):
            return {"coupons": MOCK_COUPONS}
        if name == "auto-bind-coupons":
            return {"bound": [c["name"] for c in MOCK_COUPONS], "success": True}
        if name == "query-nearby-stores":
            city = args.get("city", "上海")
            return {"stores": [
                {"name": "%s五角场店" % city, "distance": "0.8km", "selfPickup": True, "driveThru": True},
                {"name": "%s人民广场店" % city, "distance": "1.5km", "selfPickup": True, "driveThru": False},
            ]}
        if name == "query-meals":
            kw = args.get("keyword", "")
            cat = args.get("category", "")
            items = [m for m in MOCK_MENU if (not kw or kw in m["name"]) and (not cat or m["cat"] == cat)]
            return {"meals": items or MOCK_MENU}
        if name == "query-meal-detail":
            nm = args.get("name", "")
            for m in MOCK_MENU:
                if m["name"] == nm:
                    return dict(m, desc="经典麦当劳单品，%d 千卡" % m["cal"])
            return {"name": nm, "desc": "示例单品"}
        if name == "calculate-price":
            # 严格遵守官方规则：本工具返回「分」（整数），展示前 ÷100
            items = args.get("items", [])
            total_fen = 0
            for it in items:
                nm = it.get("name", "")
                qty = it.get("qty", 1)
                for m in MOCK_MENU:
                    if m["name"] == nm:
                        total_fen += int(round(m["price"] * 100)) * qty
            return {"total": total_fen, "currency": "fen", "_note": "单位为分，展示前请除以100"}
        if name == "create-order":
            return {"orderId": "DEMO-%s" % os.urandom(4).hex(), "payUrl": "https://mcd.cn/pay/demo", "status": "待支付"}
        if name == "query-my-account":
            return {"points": 1280, "level": "会员"}
        if name == "mall-points-products":
            return {"products": [
                {"name": "麦辣鸡腿堡兑换券", "points": 1200, "type": "virtual"},
                {"name": "麦当劳帆布包", "points": 3500, "type": "physical"},
            ]}
        if name == "campaign-calender":
            return {"campaigns": [
                {"name": "1+1=12.9 随心配", "status": "进行中"},
                {"name": "周末麦麦夜市半价", "status": "即将开始"},
            ]}
        return {"demo": True, "tool": name, "args": args}

    # ------------------------- 业务方法 -------------------------
    def initialize(self):
        res = self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "mcd-mcp-client", "version": "1.1"}}})
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        except SystemExit:
            pass
        return res

    def list_tools(self):
        self.initialize()
        res = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        return (res or {}).get("result", {}).get("tools", [])

    def call(self, name, arguments=None):
        self.initialize()
        return self._post({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                           "params": {"name": name, "arguments": arguments or {}}})

    def tool_json(self, name, args=None):
        """调用工具并解析出业务 JSON（兼容真实 content 包裹与 demo 直出）。"""
        r = self.call(name, args)
        if r is None:
            return {}
        if isinstance(r, dict) and "result" in r:
            content = r["result"].get("content")
            if isinstance(content, list) and content:
                txt = content[0].get("text", "{}")
                try:
                    return json.loads(txt)
                except Exception:
                    return {}
        return r

    # ------------------------- ★ 省钱最优解引擎 -------------------------
    def recommend(self, budget, city=None):
        """把 菜单 + 优惠券 + 价格试算 组合成「预算内最划算点法」。

        返回 Top3 组合：原价(元) / 用券后(元) / 省了多少 / 价值分 / 推荐理由。
        价值分 = (总千卡 + 品类数×40) / 用券后价，越高越"值"。
        """
        meals = self.tool_json("query-meals", {}).get("meals", MOCK_MENU)
        coupons = self.tool_json("my-coupons", {}).get("coupons", MOCK_COUPONS)
        by_name = {m["name"]: m for m in meals}

        mains = [m for m in meals if m["cat"] == "主食"]
        sides = [m for m in meals if m["cat"] == "小食"]
        drinks = [m for m in meals if m["cat"] == "饮料"]
        sweets = [m for m in meals if m["cat"] == "甜品"]

        combos = []
        # 单人餐：1 主食 +（小食）+（饮料）
        for main in mains:
            for side in (sides or [None]):
                for drink in (drinks or [None]):
                    pick = [main]
                    if side:
                        pick.append(side)
                    if drink:
                        pick.append(drink)
                    combos.append(pick)
        # 单人甜品胃：1 主食 + 甜品
        for main in mains:
            for sweet in (sweets or [None]):
                pick = [main]
                if sweet:
                    pick.append(sweet)
                combos.append(pick)
        # 双人分享餐：2 主食 +（小食）+（饮料）——让「买一送一」券真正生效
        for m1 in mains:
            for m2 in mains:
                for side in (sides or [None]):
                    for drink in (drinks or [None]):
                        pick = [m1, m2]
                        if side:
                            pick.append(side)
                        if drink:
                            pick.append(drink)
                        combos.append(pick)

        results = []
        for combo in combos:
            items = [{"name": c["name"], "qty": 1} for c in combo]
            price_res = self.tool_json("calculate-price", {"items": items})
            # calculate-price 返回「分」→ 转元
            yuan = (price_res.get("total", 0) or 0) / 100.0
            if yuan <= 0 or yuan > budget + 0.01:
                continue
            net, used_coupon = self._apply_best_coupon(combo, yuan, coupons)
            cal = sum(c.get("cal", 0) for c in combo)
            cats = len(set(c["cat"] for c in combo))
            value = (cal + cats * 40) / net if net > 0 else 0
            results.append({
                "combo": " + ".join(c["name"] for c in combo),
                "origin": yuan, "net": net, "saved": round(yuan - net, 2),
                "coupon": used_coupon, "cal": cal, "value": round(value, 1),
            })
        # 首要：省得最多；其次：每元获得感（划算指数）
        results.sort(key=lambda x: (x["saved"], x["value"]), reverse=True)
        return results[:3]

    @staticmethod
    def _apply_best_coupon(combo, yuan, coupons):
        best_off = 0.0
        best_name = "无可用券"
        names = [c["name"] for c in combo]
        n_mains = sum(1 for c in combo if c["cat"] == "主食")
        for cp in coupons:
            off = 0.0
            if cp.get("type") == "fullreduce" and yuan >= cp.get("threshold", 1e9):
                off = cp.get("off", 0)
            elif cp.get("type") == "itemoff" and any(cp.get("target", "") in n for n in names):
                off = cp.get("off", 0)
            elif cp.get("type") == "bogo" and n_mains >= 2 and any("堡" in n for n in names):
                # 汉堡买一送一：仅当含 ≥2 个主食(堡类)才生效，减一个最便宜主食的价
                off = min((c.get("price", 0) for c in combo if c["cat"] == "主食"), default=0)
            elif cp.get("type") == "half2" and any(cp.get("target", "") in n for n in names):
                # 甜品第二件半价：减最贵甜品一半
                sw = [c.get("price", 0) for c in combo if cp.get("target", "") in c["name"]]
                off = (max(sw) / 2) if sw else 0
            if off > best_off:
                best_off, best_name = off, cp.get("name", "券")
        return round(yuan - best_off, 2), best_name


MOCK_TOOLS = [
    {"name": "now-time-info", "description": "获取当前时间与时段的演示工具", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "available-coupons", "description": "查询麦麦省当前可领优惠券", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "auto-bind-coupons", "description": "一键领取全部可用券（写操作）", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "my-coupons", "description": "查询已到账优惠券", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "query-nearby-stores", "description": "查询附近可点餐门店", "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}, "keyword": {"type": "string"}}}},
    {"name": "query-meals", "description": "查询菜单/餐品", "inputSchema": {"type": "object", "properties": {"category": {"type": "string"}, "keyword": {"type": "string"}}}},
    {"name": "query-meal-detail", "description": "餐品详情（含营养）", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}}},
    {"name": "calculate-price", "description": "价格试算（返回单位为「分」）", "inputSchema": {"type": "object", "properties": {"items": {"type": "array"}}}},
    {"name": "create-order", "description": "下单（写操作）", "inputSchema": {"type": "object", "properties": {"items": {"type": "array"}}}},
    {"name": "query-my-account", "description": "查询账户/积分", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "mall-points-products", "description": "积分商城商品列表", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "campaign-calender", "description": "当月营销活动日历", "inputSchema": {"type": "object", "properties": {}}},
]


def _print_recommend(recs, budget):
    if not recs:
        print("😶 预算 %.1f 元内没有凑出合适组合，试着放宽预算或告知想吃的品类。" % budget)
        return
    print("\n🍔 麦麦管家 · 省钱最优解（预算 ¥%.1f）" % budget)
    print("-" * 60)
    for i, r in enumerate(recs, 1):
        print("【方案 %d】%s" % (i, r["combo"]))
        print("   原价 ¥%.2f → 用券[%s]后 ¥%.2f，省 ¥%.2f | 约 %d 千卡 | 划算指数 %.1f"
              % (r["origin"], r["coupon"], r["net"], r["saved"], r["cal"], r["value"]))
    print("-" * 60)
    print("💡 排序优先看「省多少」，其次看「划算指数=（总热量+品类×40）÷用券后价」；下单前请与麦当劳实时价格核对。")


def _sc(mcp, tool, args=None):
    """取工具返回的 structuredContent（真实模式走官方 MCP，demo 模式走内置 Mock）"""
    r = mcp.call(tool, args or {})
    return r.get("result", {}).get("structuredContent", {}) or {}


def _parse_nutrition(data_str):
    """从 list-nutrition-foods 的 data 文本里解析 (餐品名, 热量kcal) 列表"""
    rows = []
    for line in (data_str or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") or (":" in line and line.endswith(":")):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            kcal = int(parts[3])
        except ValueError:
            continue
        rows.append((parts[0], kcal))
    return rows


def brief(mcp):
    """今日麦麦情报：真实多工具编排（时间+券+活动+低卡热量），只读、无写操作。"""
    print("🍔 麦麦管家 · 今日麦麦情报（真实调用麦当劳中国官方 MCP）")
    print("=" * 64)
    # 1) 时间
    try:
        t = _sc(mcp, "now-time-info")
        td = t.get("data", t)
        print("🕐 当前时间：%s（%s）" % (td.get("formatted") or td.get("datetime"), td.get("dayOfWeek")))
    except Exception as e:
        print("🕐 时间获取失败：%s" % e)
    # 2) 可领券
    try:
        ac = _sc(mcp, "available-coupons")
        coupons = ac.get("data", []) if isinstance(ac.get("data"), list) else []
        print("\n🎟️  今日可领券（前 8 张）：")
        for c in coupons[:8]:
            print("   · %s（%s）" % (c.get("couponName"), c.get("label")))
        if len(coupons) > 8:
            print("   ……共 %d 张可领" % len(coupons))
    except Exception as e:
        print("\n🎟️  券获取失败：%s" % e)
    # 3) 活动日历
    try:
        cc = _sc(mcp, "campaign-calendar")
        daily = cc.get("data", {}).get("dailyList", []) if isinstance(cc.get("data"), dict) else []
        print("\n📅 近期活动（前 5 条）：")
        shown = 0
        for d in daily:
            for ev in d.get("events", []):
                title = (ev.get("activityTitle")
                         or (ev.get("articleDto") or {}).get("title")
                         or ev.get("activitySubTitle")
                         or ev.get("resourceId"))
                if title:
                    print("   · [%s] %s" % (d.get("dateText", "").split()[0] if d.get("dateText") else "", title))
                    shown += 1
                    if shown >= 5:
                        break
            if shown >= 5:
                break
    except Exception as e:
        print("\n📅 活动获取失败：%s" % e)
    # 4) 低卡轻食（真实热量）
    try:
        nf = _sc(mcp, "list-nutrition-foods")
        rows = _parse_nutrition(nf.get("data", ""))
        rows.sort(key=lambda x: x[1])
        print("\n🥗 低卡轻食推荐（真实热量 Top5）：")
        for name, kcal in rows[:5]:
            print("   · %s —— %d kcal" % (name, kcal))
    except Exception as e:
        print("\n🥗 热量获取失败：%s" % e)
    print("\n" + "=" * 64)
    print("💡 以上均来自麦当劳中国官方 MCP 实时返回；下单/领券请在 WorkBuddy 中确认。")


def find_stores(mcp, city="上海", keyword="人民广场"):
    """按城市+关键词搜门店，返回门店列表（供用户自选）。"""
    sr = _sc(mcp, "query-nearby-stores", {"beType": 1, "searchType": 2, "city": city, "keyword": keyword})
    return sr.get("data") or []


def _fetch_real_menu(mcp, city="上海", keyword="人民广场", store_code=None, store_index=0):
    """真实拉取门店菜单：query-nearby-stores → query-meals。

    store_code：用户自选门店（优先级最高，支持自定义价格来源）；
    store_index：未指定 store_code 时取搜索结果第几家（默认第 1 家）。
    """
    if store_code:
        # 自选门店：仍搜一次拿到门店展示信息，搜不到就用最小信息
        stores = find_stores(mcp, city, keyword) if city else []
        store = next((s for s in stores if str(s.get("storeCode")) == str(store_code)),
                     {"storeCode": store_code, "storeName": "门店 storeCode=%s" % store_code,
                      "address": "（补传 --city + --keyword 可显示门店名）"})
    else:
        stores = find_stores(mcp, city, keyword)
        if not stores:
            raise RuntimeError("未找到门店（city=%s keyword=%s），请换关键词" % (city, keyword))
        store = stores[max(0, min(store_index, len(stores) - 1))]
    mr = _sc(mcp, "query-meals", {"storeCode": store.get("storeCode"), "orderType": 1, "beType": 1})
    data = mr.get("data") or {}
    return store, data.get("meals") or {}, data.get("categories") or {}


def _classify_real_menu(meals, cats):
    """把真实菜单归类为 单人候选/双人候选（省额 = 官方原价-现价）。"""
    singles, duos = [], []
    for c in cats:
        cname = c.get("name", "") or ""
        for it in c.get("meals", []):
            m = meals.get(it.get("code"))
            if not m:
                continue
            name = m.get("name", "") or ""
            try:
                cur = float(m.get("currentPrice") or 0)
                orig = float(m.get("originalPrice") or cur)
            except (TypeError, ValueError):
                continue
            item = {"name": name, "cur": cur, "orig": orig,
                    "saved": round(orig - cur, 2), "cat": cname}
            if ("双人" in cname) or ("双人" in name) or ("分享" in cname):
                duos.append(item)
            elif ("单人" in cname) or ("套餐" in cname) or ("三件套" in name) or ("堡" in name):
                singles.append(item)
    return singles, duos


def recommend_real(mcp, budget, city, keyword, store_code=None, store_index=0):
    """真实数据驱动的省钱最优解：官方现价/原价差即省额，不做任何虚构。"""
    store, meals, cats = _fetch_real_menu(mcp, city, keyword, store_code, store_index)
    singles, duos = _classify_real_menu(meals, cats)
    cands = []
    for tag, pool in (("单人", singles), ("双人", duos)):
        for it in pool:
            if 0 < it["cur"] <= budget:
                cands.append(dict(it, tag=tag))
    cands.sort(key=lambda x: x["saved"], reverse=True)
    return store, cands[:3]


def _print_real_recs(store, recs, budget):
    print("\n🍔 麦麦管家 · 省钱最优解（预算 ¥%.1f · 真实官方价）" % budget)
    print("📍 门店：%s（%s，storeCode=%s）" % (store.get("storeName"), store.get("address"), store.get("storeCode")))
    print("-" * 64)
    if not recs:
        print("预算内暂无套餐（可调高预算或换 --keyword 换门店）")
    for i, r in enumerate(recs, 1):
        print("【方案 %d · %s餐】%s" % (i, r["tag"], r["name"]))
        print("   官方现价 ¥%.2f（原价 ¥%.2f，立省 ¥%.2f）｜分类：%s"
              % (r["cur"], r["orig"], r["saved"], r["cat"]))
    print("-" * 64)
    print("💡 省额 = 官方原价-现价（实时接口）；再叠加可领券（见 daily/brief）或 App 内券面额，能更省。")


def daily(mcp, city="上海", keyword="人民广场", store_code=None):
    """今日最划算日报：活动日历 + 可领券 + 真实菜单折扣 Top5（决策版）。"""
    print("📰 麦麦管家 · 今日吃什么最划算（真实官方数据）")
    print("=" * 64)
    try:
        td = _sc(mcp, "now-time-info")
        td = td.get("data", td)
        print("🕐 %s（%s）" % (td.get("formatted"), td.get("dayOfWeek")))
    except Exception as e:
        print("🕐 时间获取失败：%s" % e)
    try:
        cc = _sc(mcp, "campaign-calendar")
        dl = (cc.get("data") or {}).get("dailyList") or []
        today = [d for d in dl if "今日" in (d.get("dateText") or "")]
        print("\n📅 今日活动：")
        shown = 0
        for d in today:
            for ev in d.get("events", []):
                title = ev.get("activityTitle") or (ev.get("articleDto") or {}).get("title")
                if title and shown < 3:
                    print("   · %s" % title)
                    shown += 1
        if shown == 0:
            print("   · 今日无重点活动")
    except Exception as e:
        print("📅 活动获取失败：%s" % e)
    try:
        ac = _sc(mcp, "available-coupons")
        cps = ac.get("data") or []
        print("\n🎟️ 可领券（前 5）：%s" % "、".join((c.get("couponName") or "") for c in cps[:5]))
    except Exception as e:
        print("🎟️ 券获取失败：%s" % e)
    try:
        store, meals, cats = _fetch_real_menu(mcp, city, keyword, store_code)
        singles, duos = _classify_real_menu(meals, cats)
        top = sorted(duos + singles, key=lambda x: x["saved"], reverse=True)[:5]
        print("\n💰 今日最划算 Top5（%s · %s）：" % (store.get("storeName"), store.get("address")))
        for i, r in enumerate(top, 1):
            print("   %d. %s —— ¥%.1f（原 ¥%.1f，省 ¥%.1f）" % (i, r["name"], r["cur"], r["orig"], r["saved"]))
    except Exception as e:
        print("💰 菜单获取失败：%s" % e)
    print("\n" + "=" * 64)
    print("💡 数据均来自麦当劳中国官方 MCP 实时返回；下单请以 App 实际结算为准。")


def main():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--demo", action="store_true", help="离线演示模式（无需 Token）")

    p = argparse.ArgumentParser(description="麦当劳中国 MCP 客户端（零依赖）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", parents=[parent], help="初始化并验证 Token")
    sub.add_parser("list", parents=[parent], help="列出全部工具")
    c = sub.add_parser("call", parents=[parent], help="调用工具")
    c.add_argument("tool", help="工具名，如 available-coupons")
    c.add_argument("--args", default="{}", help='JSON 参数，如 \'{"city":"上海"}\'')
    s = sub.add_parser("save", parents=[parent], help="★省钱最优解引擎")
    s.add_argument("--budget", type=float, default=30.0, help="预算（元）")
    s.add_argument("--city", default="上海", help="城市")
    s.add_argument("--keyword", default="人民广场", help="门店搜索关键词（定位门店用）")
    s.add_argument("--store-code", dest="store_code", default=None, help="自选门店 storeCode（先跑 stores 命令查看）")
    s.add_argument("--store-index", dest="store_index", type=int, default=0, help="搜索结果第几家门店（0=第1家，默认）")
    sub.add_parser("demo", parents=[parent], help="打印完整演示对话")
    sub.add_parser("brief", parents=[parent], help="★今日麦麦情报（真实多工具编排）")
    st = sub.add_parser("stores", parents=[parent], help="★列出可选门店（配合 --store-code 自定义价格来源）")
    st.add_argument("--city", default="上海", help="城市")
    st.add_argument("--keyword", default="人民广场", help="门店搜索关键词")
    dly = sub.add_parser("daily", parents=[parent], help="★今日最划算日报（活动+券+真实价格）")
    dly.add_argument("--city", default="上海", help="城市")
    dly.add_argument("--keyword", default="人民广场", help="门店搜索关键词")
    dly.add_argument("--store-code", dest="store_code", default=None, help="自选门店 storeCode")

    args = p.parse_args()
    demo = bool(args.demo) or os.environ.get("MCD_DEMO") == "1"
    mcp = McdMcp(demo=demo)

    if not os.environ.get("MCD_MCP_TOKEN") and not demo:
        _err("⚠️ 未检测到 MCD_MCP_TOKEN，真实请求将被拒绝（401）。加 --demo 可离线体验。")

    if args.cmd == "init":
        print(json.dumps(mcp.initialize(), ensure_ascii=False, indent=2))
    elif args.cmd == "list":
        print(json.dumps(mcp.list_tools(), ensure_ascii=False, indent=2))
    elif args.cmd == "call":
        try:
            a = json.loads(args.args)
        except json.JSONDecodeError:
            raise SystemExit("❌ --args 不是合法 JSON")
        print(json.dumps(mcp.call(args.tool, a), ensure_ascii=False, indent=2))
    elif args.cmd == "stores":
        stores = find_stores(mcp, args.city, args.keyword)
        if not stores:
            print("未找到门店（city=%s keyword=%s），请换关键词" % (args.city, args.keyword))
        else:
            print("\n🏪 %s · 可选门店（%d 家，用 --store-code 指定）：" % (args.city, len(stores)))
            for i, st in enumerate(stores, 1):
                print("  %d. %s ｜ %s ｜ storeCode=%s"
                      % (i, st.get("storeName"), st.get("address"), st.get("storeCode")))
    elif args.cmd == "save":
        if demo:
            recs = mcp.recommend(args.budget, args.city)
            _print_recommend(recs, args.budget)
        else:
            try:
                store, recs = recommend_real(mcp, args.budget, args.city, args.keyword,
                                             args.store_code, args.store_index)
                _print_real_recs(store, recs, args.budget)
            except Exception as e:
                print("⚠️ 真实菜单获取失败（%s），退回离线演示数据：" % e)
                recs = mcp.recommend(args.budget, args.city)
                _print_recommend(recs, args.budget)
    elif args.cmd == "daily":
        daily(mcp, args.city, args.keyword, args.store_code)
    elif args.cmd == "demo":
        print(json.dumps(mcp.call("now-time-info"), ensure_ascii=False, indent=2))
        print(json.dumps(mcp.call("available-coupons"), ensure_ascii=False, indent=2))
        _print_recommend(mcp.recommend(30, "上海"), 30)
    elif args.cmd == "brief":
        brief(mcp)


if __name__ == "__main__":
    main()
