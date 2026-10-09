#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦当劳中国 MCP 零依赖客户端（Streamable HTTP / JSON-RPC 2.0）。

仅用 Python 标准库，Windows / macOS / Linux 通用。
前置：设置环境变量 MCD_MCP_TOKEN（https://open.mcd.cn/mcp 申请），可选 MCD_MCP_URL。

用法：
  python mcd_mcp.py init                                       # 初始化并验证 Token
  python mcd_mcp.py list                                       # 列出全部 24 个工具及参数
  python mcd_mcp.py call <tool> [--args '<json>']              # 调用工具
示例：
  python mcd_mcp.py call available-coupons
  python mcd_mcp.py call query-nearby-stores --args '{"city":"上海"}'
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

DEFAULT_URL = "https://mcp.mcd.cn"
PROTOCOL = "2025-06-18"


def _err(msg):
    print(msg, file=sys.stderr)


class McdMcp:
    def __init__(self, url=None, token=None):
        self.url = (url or os.environ.get("MCD_MCP_URL") or DEFAULT_URL).rstrip("/")
        self.token = token if token is not None else os.environ.get("MCD_MCP_TOKEN")
        self.session_id = None

    def _post(self, payload, extra_headers=None):
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "mcd-mcp-client/1.0",
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
                    "❌ %d：Token 缺失/未被接受（未鉴权请求会被网关拒绝）。请到 https://open.mcd.cn/mcp 登录获取并写入 MCD_MCP_TOKEN"
                    % e.code
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

    def initialize(self):
        res = self._post({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "mcd-mcp-client", "version": "1.0"},
            },
        })
        # 发送 initialized 通知（无 id，服务器通常返回 202 空体）
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
        res = self._post({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        return res


def main():
    p = argparse.ArgumentParser(description="麦当劳中国 MCP 客户端（零依赖）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="初始化并验证 Token")
    sub.add_parser("list", help="列出全部工具")
    c = sub.add_parser("call", help="调用工具")
    c.add_argument("tool", help="工具名，如 available-coupons")
    c.add_argument("--args", default="{}", help='JSON 参数，如 \'{"city":"上海"}\'')
    args = p.parse_args()

    if not os.environ.get("MCD_MCP_TOKEN"):
        _err("⚠️ 未检测到 MCD_MCP_TOKEN，请求将被拒绝（401）。请先设置环境变量后再调用。")

    mcp = McdMcp()
    if args.cmd == "init":
        r = mcp.initialize()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "list":
        tools = mcp.list_tools()
        print(json.dumps(tools, ensure_ascii=False, indent=2))
    elif args.cmd == "call":
        try:
            a = json.loads(args.args)
        except json.JSONDecodeError:
            raise SystemExit("❌ --args 不是合法 JSON")
        r = mcp.call(args.tool, a)
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
