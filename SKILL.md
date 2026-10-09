---
name: mcd-mcp
description: 用麦当劳中国官方 MCP（mcp.mcd.cn）完成点餐推荐、优惠券查询与一键领取、积分商城兑换、门店与菜单查询、活动日历。当用户提到麦当劳、McDonald's、麦乐送、麦麦省、麦当劳优惠券、麦当劳积分、麦当劳点餐、附近麦当劳门店、麦麦商城时启用。可作为麦当劳中国「1024 程序员节创意开发大赛」的参赛作品（基于麦当劳 MCP 构建创意 Skill，使用 WorkBuddy 参赛有特别奖励）。
---

# 麦当劳中国 MCP 技能

把麦当劳中国官方 MCP 服务（[open.mcd.cn/mcp](https://open.mcd.cn/mcp)）封装成可复用能力：让 Agent 能查菜单、算价格、推荐套餐、查领优惠券、查门店、查积分、逛麦麦商城并下单。所有调用走官方 MCP，不碰用户密码，支付由用户在麦当劳 App 自行完成。

## 服务概况

- 提供方：麦当劳中国，覆盖中国大陆（不含港澳台）。
- 端点：`https://mcp.mcd.cn`，传输 **Streamable HTTP**，协议 `2025-06-18`。
- 工具数：24 个；限流：每 Token 每分钟 600 次（超限返回 `429`）。
- 鉴权：请求头 `Authorization: Bearer <MCD_MCP_TOKEN>`。Token 缺失/过期 → `401`。

## 前置：获取 Token（一次性）

1. 打开 https://open.mcd.cn/mcp ，用手机号登录。
2. 进入「控制台」→「激活」→ 同意服务协议。
3. 复制 Token，写入环境变量 `MCD_MCP_TOKEN`。
4. ⚠️ 不要把 Token 写进会被提交/分享的文件，也不要在对话、日志中展示明文。

## 两种执行方式（任选其一）

**方式 A — WorkBuddy 原生 MCP（推荐，最顺手）**
把以下配置合并进 `~/.workbuddy/mcp.json`（Windows：`%USERPROFILE%\.workbuddy\mcp.json`），注意把 Token 填进 headers，或让 WorkBuddy 读取环境变量：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer 你的MCD_MCP_TOKEN" }
    }
  }
}
```

**方式 B — 零依赖 Python 客户端（任何环境都能跑，含 WorkBuddy Craft 模式）**
WorkBuddy 用 Bash/执行命令跑 `scripts/mcd_mcp.py`：

```bash
export MCD_MCP_TOKEN="你的token"
python scripts/mcd_mcp.py list                       # 列出 37 个工具及参数
python scripts/mcd_mcp.py save --budget 60            # ★省钱最优解（真实官方价）
python scripts/mcd_mcp.py stores --city 北京 --keyword 王府井   # ★列出可选门店
python scripts/mcd_mcp.py save --budget 60 --city 北京 --store-code 1950526   # ★自选门店算价
python scripts/mcd_mcp.py daily                       # ★今日最划算日报（活动+券+真实价）
python scripts/mcd_mcp.py brief                       # 今日麦麦情报（时间+券+活动+热量）
python scripts/mcd_mcp.py call available-coupons      # 查可领券
python scripts/mcd_mcp.py call auto-bind-coupons      # 一键领券（写操作，先确认）
python scripts/mcd_mcp.py call query-nearby-stores --args '{"beType":1,"searchType":2,"city":"上海","keyword":"人民广场"}'
```
> 注意：`query-nearby-stores` 的 `city` 和 `keyword` **必须同时提供**，只传 city 会报「城市名或者关键词不能为空」。
> **门店自定义**：用户想指定门店时，先跑 `stores --city X --keyword Y` 列出门店（含 storeCode），再用 `--store-code` 或 `--store-index`（第几家）算价；同一套餐不同门店原价不同（实测双人餐原价上海 114.5 / 北京 117.0 / 广州 115.0），务必以所选门店价格为准。

## 调用原则

- **先查后做**：任何写操作（领券、下单、兑换、建地址）前，先和用户确认动作与参数。
- **工具名用官方原名**：`query-meals`、`calculate-price`、`create-order` 等，不要改写。
- **运行时 schema 优先**：参数细节以 `tools/list` 实时返回为准；本技能只给业务编排与坑位提示。
- **服务器返回的工具描述优先于本文档**。

## ⚠️ 价格单位大坑（必读）

价格单位**按工具区分**，不要一概除以 100：

- **仅** `calculate-price` 返回的价格是「分」（无引号整数），展示前除以 100。
- `query-meals`、`query-meal-detail`、`create-order`、`query-order` 及麦麦商城订单返回的金额已是「元」字符串，直接展示。
- 所有积分字段（`points`、`totalPoints` 等）不按金额换算。

## 场景工作流

### 0. ★ 省钱最优解引擎（核心创新）
用户给预算（如"60 块配两个人吃的怎么点最省"）→ 引擎自动走 `query-nearby-stores`（定位门店，city+keyword 必须同传）→ `query-meals`（拉 119 项真实餐品，含 `currentPrice`/`originalPrice`）→ 按官方折扣（原价-现价）排序，单人餐/双人餐分类输出 Top3。CLI：`python scripts/mcd_mcp.py save --budget 60`（真实官方价；加 `--demo` 离线演示；失败自动退回演示数据）。**省额全部来自官方数据，无虚构**。这是本项目区别于"纯工具封装"的关键，务必优先展示。

### 0.5 ★ 今日最划算日报（daily）
用户问"今天吃什么划算/有什么优惠"→ CLI：`python scripts/mcd_mcp.py daily`（一次编排 `now-time-info` + `campaign-calendar` 今日活动 + `available-coupons` 可领券 + `query-meals` 折扣 Top5）。轻量情报用 `brief`（不含价格）。

### 1. 智能点餐推荐
`now-time-info`（拿当前时间）→ `query-nearby-stores`（选定门店，到店自提/得来速/麦乐送）→ `query-meals`（按品类/关键词查餐品）→ 结合用户口味/预算给推荐 → `calculate-price`（核价，注意除以 100）→ 确认后 `create-order`。

### 2. 优惠券聚合与一键领取
`available-coupons`（看麦麦省当前可领券）→ 告知用户 → 确认后 `auto-bind-coupons`（一键领所有可用券）→ `query-my-coupons`（展示已到账券）。

### 3. 附近门店查询
`query-nearby-stores`（到店自提场景，支持 city / keyword 过滤）→ 返回可点餐门店列表。

### 4. 积分商城兑换
`query-my-account`（查积分余额）→ `mall-points-products`（逛积分商城）→ `mall-product-detail`（看详情）→ 确认后 `mall-create-order`（用 `spuCategory` 区分：1=虚拟券、2=实物，实物需 addressId）。

### 5. 活动日历
`campaign-calendar` 查询当月营销活动（进行中/往期/未来），用于结合活动给出点餐或领券建议。

## 隐私与安全

- 写操作会改变外部账户状态，必须在用户明确确认后才调用；浏览/咨询阶段不要触发。
- 新增地址会向麦当劳发送姓名、手机号、详细地址；只收集任务必需数据，展示手机号时脱敏（如 `152****6666`）。
- 支付由用户在返回的链接或麦当劳 App 自行完成，Agent 不代付。
- 任何情况下都不在回答、日志、命令参数或文件中暴露 `MCD_MCP_TOKEN`。

## 错误处理

- `401`：Token 缺失/过期 → 提示去 open.mcd.cn/mcp 重新获取。
- `429`：限流（600 次/分）→ 稍后重试。
- 网络/超时：提示检查网络后重试。
- 工具返回业务错误：原样转述给用户，不臆造结果。

## 完整工具清单

见 `references/tools.md`（含已确认工具的中文用途与入参要点；其余工具用 `python scripts/mcd_mcp.py list` 实时查看）。
