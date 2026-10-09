# 麦麦管家 mcd-butler 🍔

> 基于麦当劳中国官方 MCP 的全能点餐助手：查券一键领、套餐智能推荐、积分不浪费、门店活动全知道。

## 项目介绍

「麦麦管家」是一个运行在 WorkBuddy（及其他支持 MCP 的 Agent）里的 Skill，接入**麦当劳中国官方 MCP Server**（`https://mcp.mcd.cn`，24 个工具），把"翻 App 比价、找券、查积分"的完整决策链路压缩成一句话：

- **麦门省钱**：一句话查当前可领券 → 确认后一键领券 → 按券面规则推荐"怎么点最省"。
- **智能套餐推荐**：说出预算和时段，自动查门店、菜单、试算价格（注意分/元换算），给出 2-3 套组合和推荐理由。
- **积分不浪费**：查积分余额 → 逛积分商城 → 确认后兑换虚拟券或实物。
- **附近门店 & 活动日历**：结合当月营销活动和附近门店，输出"什么时候去、去哪家、吃什么"。

写操作（领券、下单、兑换）全部需要用户明确确认后才执行；支付由用户在麦当劳 App 自行完成。

## 安装方法

### 方式 A：WorkBuddy 自定义连接器（推荐）

1. 到 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 用手机号登录，控制台 → 激活，复制 MCP Token。
2. WorkBuddy 左侧边栏【专家·技能·连接器】→【连接器】→ 右上角【自定义连接器】→【配置MCP】，填入：

   ```json
   {
     "mcpServers": {
       "mcd-mcp": {
         "type": "streamablehttp",
         "url": "https://mcp.mcd.cn",
         "headers": {
           "Authorization": "Bearer YOUR_MCP_TOKEN"
         }
       }
     }
   }
   ```

   把 `YOUR_MCP_TOKEN` 替换为你的实际 Token，保存后启用 `mcd-mcp`。
3. 把本仓库的 `SKILL.md`、`references/`、`scripts/` 复制到 `%USERPROFILE%\.workbuddy\skills\mcd-butler\`，重启 WorkBuddy。

### 方式 B：零依赖 Python 客户端（任何环境可跑）

```bash
export MCD_MCP_TOKEN="你的token"        # Windows PowerShell: $env:MCD_MCP_TOKEN="你的token"
python scripts/mcd_mcp.py init          # 验证 Token
python scripts/mcd_mcp.py list          # 列出全部 24 个工具
python scripts/mcd_mcp.py call available-coupons
python scripts/mcd_mcp.py call auto-bind-coupons
python scripts/mcd_mcp.py call query-nearby-stores --args '{"city":"上海"}'
```

仅用 Python 标准库，无需安装任何第三方包。

## 使用示例

装好后在 WorkBuddy 里直接说：

- 「麦当劳现在有什么券可领？帮我领了」
- 「30 块以内帮我配一套晚饭，附近哪家店？」
- 「我的积分能换啥？」
- 「这个月麦当劳有什么活动？」

或用 CLI：

```bash
python scripts/mcd_mcp.py call my-coupons
python scripts/mcd_mcp.py call calculate-price --args '{"items":[...]}'
```

## 目标用户

- **打工人 / 学生**：想吃麦当劳但不想翻 App 比价的"麦门"信徒，核心诉求是省钱、省时间。
- **麦当劳会员**：手里有券、有积分但经常忘记用的人，需要有人提醒并代办。
- **Agent / MCP 开发者**：想要一个接入真实商业 MCP 的参考实现（含零依赖 Streamable HTTP 客户端、SSE 解析、写操作确认流程）。

## 文件结构

```
mcd-butler/
├── README.md                 # 本文件
├── CONTEST_DECLARATION.md    # 参赛声明（官方原文）
├── MCP_INTEGRATION.md        # MCP Server / Tool / 调用流程 / 业务价值
├── workbuddy.md              # WorkBuddy 开发对话上下文
├── SKILL.md                  # 技能主体（Agent 运行时加载）
├── references/tools.md       # 工具清单与注意事项
└── scripts/mcd_mcp.py        # 零依赖 Python MCP 客户端
```

## 参赛说明

本项目为**麦当劳程序员节创意开发大赛**参赛作品（2026-10-09 报名），基于麦当劳中国官方 MCP 能力开发，非麦当劳官方产品。餐品信息、价格及供应状态以麦当劳官方渠道的实时结果为准。

- 官方赛事仓库：[M-China/mcd-developer-innovation-challenge](https://github.com/M-China/mcd-developer-innovation-challenge)
- MCP 使用指南：[M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)
