# workbuddy.md — WorkBuddy 开发对话上下文

本项目由 **WorkBuddy**（腾讯全场景 AI 智能体，本次活动官方合作伙伴）辅助开发。本文档为本次开发会话的上下文记录，用于核验 WorkBuddy 联动活动奖励条件。

- 开发日期：2026-10-09
- 开发环境：WorkBuddy 桌面端（Windows），Agent 模式
- 项目：麦麦管家（mcd-butler）——基于麦当劳中国官方 MCP 的全能 Skill

---

## 第一步：赛事调研

**用户指令：**

> 搜索 workbuddy 和麦当劳的开发大赛，然后参赛

**WorkBuddy 执行：**

1. 多轮网络检索，定位到麦当劳中国「1024 程序员节创意开发大赛」：主题为基于麦当劳 MCP 能力开发创意 Skill，使用 WorkBuddy 开发可参与专项奖励。
2. 检索确认麦当劳 MCP 为真实公开服务：端点 `https://mcp.mcd.cn`，Streamable HTTP，24 个工具，覆盖点餐、优惠券、积分商城、门店、活动日历；Token 经 open.mcd.cn/mcp 实名申请。

## 第二步：端点实测（先验证再动手）

**WorkBuddy 执行：**

- 用 Python 标准库向 `https://mcp.mcd.cn/mcp-servers/mcd-mcp` 发送 MCP `initialize` 请求（协议版本 2025-06-18）。
- 实测结果：无凭据请求返回 `HTTP 403`（WAF 网关拦截，返回 `{"code":"0001","msg":"系统错误"}`）；更换浏览器 User-Agent 复测仍 403，排除 UA 拦截。
- 结论：端点真实在线，鉴权门有效（Bearer Token 必须），未持 Token 无法调用——与官方文档描述的 401/403 行为一致。

## 第三步：资料核实

**WorkBuddy 执行：**

- 抓取麦当劳 MCP 接入资料，核实关键事实：
  - 端点 `https://mcp.mcd.cn`，Streamable HTTP，协议 `2025-06-18`
  - 24 个工具；限流每 Token 每分钟 600 次（超限 429）
  - Token 经 open.mcd.cn/mcp 手机号登录 → 控制台激活获取，环境变量 `MCD_MCP_TOKEN`
  - **价格单位坑**：仅 `calculate-price` 返回「分」（展示前 ÷100），其余订单/餐品金额已是「元」字符串
  - 写操作清单：`auto-bind-coupons`、`create-order`、`mall-create-order`、`mall-create-order-physical`、`delivery-create-address`

## 第四步：技能开发

**用户确认方向后，WorkBuddy 直接产出参赛作品，创建以下文件：**

1. `SKILL.md` —— 技能主体（OpenClaw/WorkBuddy 兼容格式）：5 类场景工作流（省钱查领券 / 智能套餐推荐 / 积分商城兑换 / 附近门店 / 活动日历）、调用原则、价格单位提醒、写操作红线、隐私与错误处理。
2. `scripts/mcd_mcp.py` —— 零依赖 Python MCP 客户端：标准库实现 Streamable HTTP + JSON-RPC 2.0，含 SSE 响应解析、`Mcp-Session-Id` 会话管理、401/403/429 友好报错，Windows/macOS/Linux 通用。命令：`init` / `list` / `call <tool> --args '<json>'`。
3. `references/tools.md` —— 工具清单、入参要点、写操作红线、价格单位说明。
4. `README.md` —— 安装与使用文档。

## 第五步：验证

**WorkBuddy 执行：**

- `py_compile` 语法校验：通过。
- 无 Token 试运行 `init`：按设计优雅退出，输出「Token 缺失/未被接受，请到 open.mcd.cn/mcp 获取并写入 MCD_MCP_TOKEN」，无崩溃、无明文 Token 泄漏路径。
- 端点连通性：已实测（见第二步），真实工具调用需开发者本人 Token（官方实名机制，无法也不应代为申请）。

## 第六步：对照官方规则补齐参赛材料

**用户提供了官方活动海报，WorkBuddy 抓取 `M-China/mcd-developer-innovation-challenge` 仓库完整规则后补齐：**

- 核对必备文件清单：README.md（项目介绍/安装方法/使用示例/目标用户）、CONTEST_DECLARATION.md（官方原文，未改动）、MCP_INTEGRATION.md（Server/Tool/调用流程/业务价值）、源代码、workbuddy.md（本文档）。
- `CONTEST_DECLARATION.md` 逐字取自官方仓库 raw 文件，未做任何修改。
- 项目初始化为 Git 仓库，准备发布至个人 GitHub 公开仓库并通过官方 Issue 模板报名。

## 产出清单

```
mcd-butler/
├── README.md                 # 项目介绍、安装方法、使用示例、目标用户
├── CONTEST_DECLARATION.md    # 参赛声明（官方原文，未改动）
├── MCP_INTEGRATION.md        # MCP Server/Tool/调用流程/业务价值
├── workbuddy.md              # 本文档：WorkBuddy 开发对话上下文
├── SKILL.md                  # 技能主体（Agent 加载）
├── references/tools.md       # 37 个真实工具清单（实测校准版）
├── scripts/mcd_mcp.py        # 零依赖 MCP 客户端 + 省钱引擎 + 今日情报
├── evidence-real.md          # 真实调用证据（init/工具清单/brief 实跑）
└── demo/                     # 演示材料（index.html 交互页 + sample_run.md）
```

---

## 第七步：质量升级（冲刺获奖浓度）

**用户反馈："要质量高有获奖的可能" —— WorkBuddy 对初版做诚实体检后，认定原版是"24 工具薄封装"，缺记忆点与真实差异化，遂进行以下升级：**

1. **新增「省钱最优解引擎」（`scripts/mcd_mcp.py` 的 `recommend()`）** —— 把菜单、价格试算、优惠券三类工具**编排成一次决策**：枚举单人餐/双人分享餐组合 → `calculate-price` 核价（严守分/元规则）→ 匹配满减/买一送一/单品立减/第二件半价 → 输出省得最多 + 吃得最值的 Top3。这是区别于"纯工具封装"的核心创新。
2. **新增离线 Demo 模式（`--demo` / `MCD_DEMO=1`）** —— 内置真实感 Mock 数据，无 Token 也能跑通 `init/list/call/save` 全流程。评委/访客不填凭据即可验证项目可用，降低拿 Star 的门槛。
3. **新增可交互演示页 `demo/index.html`** —— 纯前端、无网络、无 Token，浏览器打开填预算即看推荐结果（算法与 Python 端保持一致），作为 GitHub README 的直观入口。
4. **修正 Demo 逻辑 bug** —— 初版"买一送一"会被错误作用在单个汉堡+冰淇淋上凭空省 22 元；改为仅在组合含 ≥2 个主食（堡类）时生效，并补充双人分享餐组合，确保逻辑真实可信。
5. **重写 README 与 SKILL.md / MCP_INTEGRATION.md** —— 一号卖点改为引擎而非工具列表；README 新增"冲奖策略"章节（榜单按 Star 定名次，先让人愿意点 Star 再谈质量）。

**本轮验证：**

- `py_compile` 语法校验：通过。
- 离线引擎实测（预算 ¥60）：正确命中"买一送一"（麦辣鸡腿堡×2 + 玉米杯 + 红茶，原价 ¥60 → 用券后 ¥38.50，省 ¥21.50），且无券可命中时如实显示"无可用券"（预算 ¥30 场景），逻辑自洽。
- `demo/sample_run.md` 由真实 CLI 输出生成，`demo/index.html` 在浏览器中可独立运行（已离线自检数据结构）。

**剩余需用户本人完成（AI 不能代劳）：**

- 发布到个人 GitHub 公开仓库、通过官方 Issue 报名、拉 Star（Star>0 才进榜）。

---

## 第八步：真实联调官方 MCP（Token 到位后）

**用户提供 MCP Token 后，WorkBuddy 完成真实联调（全程只读，无任何写操作）：**

1. **握手验证**：`initialize` 返回 `serverInfo: mcd-mcp v1.0.0`（协议 2025-06-18），Token 有效。
2. **工具清单实测**：`list` 返回 **37 个真实工具**（多于早期资料的 24 个），含派对线（`query-party-*` 5 个）、抽奖（`draw-lottery`/`query-lottery-info`）、营养热量（`list-nutrition-foods`，170+ 真实餐品 kcal）等。据此将 `references/tools.md` 重写为实测校准版。
3. **真实数据抓取**：`available-coupons` 返回 9 张真实可领券（麦旋风任选/薯薯任选/免费脆薯饼/人气麦旋风买一送一/9.9 元中杯冰美式等）；`campaign-calendar` 返回 10/7–10/23 真实活动（麦当劳 X PEACEMINUSONE 联名、韩式风味蘸酱、9.9 元早餐两件套等）；`now-time-info` 返回服务器时间；`list-nutrition-foods` 返回 170+ 餐品真实热量表。
4. **新增 `brief` 命令（真实多工具编排）**：把时间 + 券 + 活动 + 低卡热量四个工具的真实返回编排成"今日麦麦情报"一次输出，作为"多工具编排"能力的实跑证据。
5. **入参结构实测修正**：`now-time-info` 时间字段在 `structuredContent.data` 子对象；`campaign-calendar` 活动标题优先取 `activityTitle`、为空取 `articleDto.title`。`query-meals` 真实 schema 含 `currentPrice`/`originalPrice`，确认为省钱引擎接入真实价格的接口点（需门店参数）。
6. **生成 `evidence-real.md`**：完整记录 init 握手、37 工具清单、brief 实跑输出与合规说明；README 新增"真实调用证据"章节。

**本轮验证：** `py_compile` 通过；`init` / `list` / `brief` 真实调用全部成功；全程仅调用只读工具（`now-time-info` / `available-coupons` / `campaign-calendar` / `list-nutrition-foods`），未触发下单、领券、抽奖等任何写操作。

---

## 第九步：发布开源与官方报名（AI 经用户授权代操作）

**用户提供 GitHub PAT（repo 权限）并明确授权后，WorkBuddy 完成发布与报名闭环：**

1. PAT 经 GitHub API 验证有效（用户 `FPVMaster`，scope：repo/workflow）；Token 仅用于本次命令行调用，未写入任何仓库文件。
2. 创建公开仓库 **https://github.com/FPVMaster/mcd-butler**。
3. 推送 `main` 分支（3 个提交：初版 `2abd3ce` → 质量升级 `69f8593` → 真实联调 `4319d16`），并配置本地 remote 便于后续更新。
4. 在官方赛事仓库按既有报名 Issue 格式提交报名：**[M-China/mcd-developer-innovation-challenge#52](https://github.com/M-China/mcd-developer-innovation-challenge/issues/52)**（【参赛申请】+ 项目名称/地址/简介，与仓库内既有报名格式一致）。

**至此参赛硬性流程全部完成**，剩余为运营动作：拉 Star（10-26 00:00 按 Star 数定榜，Star>0 进榜）。
