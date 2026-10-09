# MCP 接入说明（MCP_INTEGRATION.md）

本文档说明本项目实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值。

## 一、使用的 MCP Server

| 项目 | 说明 |
|---|---|
| 服务名称 | 麦当劳中国官方 MCP Server |
| 端点 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP（MCP 协议版本 `2025-06-18`，JSON-RPC 2.0） |
| 提供方 | 麦当劳中国（覆盖中国大陆，不含港澳台） |
| 工具数量 | **37 个**（经运行时 `tools/list` 实测，见 [evidence-real.md](evidence-real.md)） |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCD_MCP_TOKEN>`，Token 在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 用手机号登录后于控制台激活获取 |
| 限流 | 每 Token 每分钟 600 次，超限返回 `429` |
| 官方文档 | [M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server) |

## 二、实际使用的 Tool 清单

本项目围绕「省钱 + 点餐 + 会员权益」三条主线编排以下工具：

| Tool | 用途 | 在本项目中的角色 |
|---|---|---|
| `now-time-info` | 获取当前时间 | 判断时段（早餐/正餐/下午茶），推荐何时段套餐 |
| `available-coupons` | 查询麦麦省可领券列表 | 省钱主线入口：先看有什么券 |
| `auto-bind-coupons` | 一键领取全部可用券（写操作） | 用户确认后执行，券自动到账 |
| `my-coupons`（实测名 `query-my-coupons`） | 查询已到账优惠券 | 展示可用券，与点餐推荐联动 |
| `campaign-calendar` | 查询当月营销活动日历 | 结合活动给出"什么时候吃最划算"建议 |
| `query-nearby-stores` | 查询附近可点餐门店 | 到店自提/得来速场景选门店（**city+keyword 必须同传**） |
| `query-meals` | 查询菜单/餐品 | 按品类、关键词取餐品数据（含 `currentPrice`/`originalPrice` 真实价格） |
| `list-nutrition-foods` | 170+ 餐品真实热量/营养表 | 划算指数与低卡推荐 |
| `query-meal-detail` | 餐品详情（含营养信息） | 推荐理由与营养参考 |
| `calculate-price` | 价格试算 | 套餐组合核价（注意：返回单位为「分」，展示前 ÷100） |
| `create-order` | 下单（写操作） | 用户确认后生成订单，支付由用户在麦当劳 App 完成 |
| `query-order` | 订单查询 | 查询订单状态 |
| `query-my-account` | 查询账户/积分 | 积分余额展示 |
| `mall-points-products` / `mall-product-detail` | 积分商城浏览/详情 | "积分别浪费"兑换推荐 |
| `mall-create-order` | 积分兑换下单（写操作，`spuCategory` 1=虚拟券/2=实物） | 用户确认后兑换 |
| `delivery-query-addresses` | 查询配送地址 | 麦乐送场景选地址 |

其余 MCP 工具以运行时 `tools/list` 实时返回的 schema 为准，技能按需调用。

## 三、核心调用流程

### 场景 1：麦门省钱（查券 → 领券 → 用券推荐）

```
用户："麦当劳现在有什么券？"
→ available-coupons        # 拉取可领券列表
→ 用户确认
→ auto-bind-coupons        # 一键领券（写操作，需确认）
→ my-coupons               # 展示到账券
→ query-meals + calculate-price   # 结合券面规则推荐"用哪张券怎么点最省"
```

### 场景 2：智能套餐推荐

```
用户："30 块钱以内帮我配一套晚饭"
→ now-time-info            # 确认时段
→ query-nearby-stores      # 选定门店
→ query-meals              # 取餐品数据
→ calculate-price          # 组合试算（分→元）
→ 输出 2-3 套组合 + 推荐理由，确认后 create-order
```

### 场景 3：积分不浪费

```
用户："我的积分能换啥？"
→ query-my-account         # 查积分余额
→ mall-points-products     # 浏览积分商城
→ mall-product-detail      # 详情
→ 用户确认后 mall-create-order / mall-create-order-physical
```

### 场景 4：活动日历 + 附近门店

```
→ campaign-calender        # 本月活动
→ query-nearby-stores      # 附近门店
→ 输出"什么时候去、去哪家、吃什么"的组合建议
```

## 四、业务价值

1. **省钱确定性强**：把"翻 App 找券"变成"一句话查券、领券、按券点餐"，券 + 活动 + 价格试算三合一，直接输出最优点餐组合。
2. **决策链路完整**：从时段、门店、菜单、价格到下单，一条对话内闭环，不需要在多个页面之间跳转。
3. **会员权益激活**：积分商城兑换入口前置，让沉睡积分变成可感知的价值。
4. **可复用的工程封装**：提供零依赖 Python 客户端（标准库实现 Streamable HTTP + SSE 解析 + 会话管理 + 401/403/429 处理），任何支持 MCP 或能跑 Python 的 Agent 框架都能直接接入。

## 五、安全与合规

- 写操作（领券、下单、兑换、新增地址）**必须经用户明确确认**后才调用；浏览/咨询阶段不触发。
- Token 仅通过环境变量 `MCD_MCP_TOKEN` 注入，任何文件、日志、对话中不出现明文 Token。
- 支付环节由用户在返回链接或麦当劳 App 自行完成，Agent 不代付。
- 展示手机号等个人信息时脱敏（如 `152****6666`）。

## 六、核心创新：省钱最优解引擎（`recommend_real`）

本项目区别于"纯工具封装"的关键能力。它把多个 MCP 工具**编排成一次决策**，而非串行调接口：

1. `query-nearby-stores`（beType=1 自提 + searchType=2 + city+keyword）定位门店，取 `storeCode`；
2. `query-meals` 拉取该店 **119 项真实餐品**，含官方 `currentPrice`（现价）/ `originalPrice`（原价）；
3. 按官方折扣（原价-现价）排序，分「单人餐 / 双人餐」输出预算内 Top3——**省额全部来自官方数据，无任何虚构**；
4. 叠加提示：`available-coupons` 可领券（券面额无结构化数据，以 App 内为准）。

实跑证据（2026-10-09 · 上海黄浦华旭国际大厦店）：预算 ¥60 → 「全明星双人分享餐八件套」¥49.9（原 ¥114.5，**立省 ¥64.6**）。完整输出见 [evidence-real.md](evidence-real.md)。

另附 **daily 日报**（`now-time-info` + `campaign-calendar` 今日活动 + `available-coupons` + `query-meals` 折扣 Top5 一次编排）与 **brief 情报**（时间+券+活动+170 项真实营养热量），覆盖"今天吃什么划算"的高频决策场景。

## 七、离线演示模式（无需 Token）

任何命令后加 `--demo`（或设环境变量 `MCD_DEMO=1`），客户端走内置真实感 Mock 数据，完整跑通 `init / list / call / save` 全流程，便于：

- 评委/访客无 Token 即可验证项目可用（对应 `demo/index.html` 交互页与 `demo/sample_run.md` 样本）；
- 开发者在拿到官方 Token 前先验证编排逻辑；
- CI / 文档截图，无需泄露任何凭据。

Mock 数据仅用于演示，标注清晰，不参与真实计费。
