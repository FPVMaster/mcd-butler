# 麦当劳中国 MCP 工具清单（references/tools.md）

> 官方服务 **`mcd-mcp v1.0.0`**，经运行时 `python scripts/mcd_mcp.py list` 实测共 **37 个工具**（多于早期资料的 24 个）。下方为按业务分组的真实工具名与用途。
> **完整入参/出参 schema 以运行时 `list` 返回的 JSON 为准**（服务器描述优先于本文档）。
> 端点：`https://mcp.mcd.cn/mcp-servers/mcd-mcp`（Streamable HTTP，协议 2025-06-18）。

## 分组清单（37 个，标 ⚠️ 为写操作）

### 🕐 时间 / 门店
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `now-time-info` | 获取服务器当前时间（日期/星期/时区），供模型判断时段 | 读 |
| `query-nearby-stores` | 按定位查询可点餐门店（含 storeCode/beCode、是否支持预约） | 读 |
| `delivery-query-stores` | 麦乐送可配送门店查询 | 读 |
| `query-store-coupons` | 指定门店可用券 | 读 |

### 🍔 餐品 / 营养 / 促销 / 核价
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `query-meals` | 菜单/餐品（分类、code、标签、现价 `currentPrice`、原价 `originalPrice`、优惠类型） | 读 |
| `query-meal-detail` | 单个餐品详情 | 读 |
| `query-meal-assistance` | 餐品辅助信息 | 读 |
| `list-nutrition-foods` | **170+ 餐品真实热量/营养表**（productName、energyKcal 等） | 读 |
| `query-promotions` | 促销活动查询 | 读 |
| `calculate-price` | 价格试算（**返回单位为「分」，展示 ÷100**） | 读 |

### 🎟️ 优惠券
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `available-coupons` | 当前可领取的麦麦省优惠券列表（couponName/状态） | 读 |
| `query-my-coupons` | 我账户里可用的券 | 读 |
| `query-store-coupons` | 门店券（见上） | 读 |
| `query-survey-coupon` | 问卷/调研券 | 读 |
| `auto-bind-coupons` | 一键领取所有可用券 | ⚠️ 写 |

### 🧾 订单
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `create-order` | 下单（到店自取/得来速/麦乐送），金额单位「元」 | ⚠️ 写 |
| `query-order` | 订单查询（金额「元」） | 读 |
| `order-list` | 我的订单列表 | 读 |
| `cancel-order` | 取消订单 | ⚠️ 写 |

### 🛍️ 积分商城
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `mall-points-products` | 浏览积分可兑换商品 | 读 |
| `mall-product-detail` | 积分商品详情 | 读 |
| `mall-create-order` | 积分兑换下单（虚拟券/实物，shopId=2） | ⚠️ 写 |
| `mall-order-list` | 积分订单列表 | 读 |
| `mall-order-detail` | 积分订单详情 | 读 |

### 🎉 活动 / 抽奖
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `campaign-calendar` | 当月营销活动日历（进行中/往期/未来，含 GD 联名等） | 读 |
| `query-lottery-info` | 抽奖活动信息 | 读 |
| `draw-lottery` | 参与抽奖 | ⚠️ 写（有成本/风险，慎调） |

### 🎂 派对（生日/主题）
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `query-party-city` | 派对开通城市 | 读 |
| `query-party-store` | 派对门店 | 读 |
| `query-party-store-date` | 派对门店可约日期 | 读 |
| `query-party-store-session` | 派对门店场次 | 读 |
| `party-order-create` | 派对下单（需选门店+场次） | ⚠️ 写 |

### 👤 账户 / 地址 / 奖品
| 工具名 | 用途 | 读/写 |
|---|---|---|
| `query-my-account` | 账户/积分余额 | 读 |
| `query-my-prizes` | 我的奖品 | 读 |
| `delivery-query-addresses` | 已保存配送地址 | 读 |
| `delivery-create-address` | 新增配送地址（**涉隐私：姓名/手机号/地址**） | ⚠️ 写 |

## 写操作红线（必须用户明确确认）

以下工具会改变外部账户状态或外发隐私数据，**仅在用户明确确认后调用**，且不得在无人值守/批量场景自动触发：

- `auto-bind-coupons`（领券）
- `create-order` / `cancel-order`（下单/取消）
- `mall-create-order`（积分兑换）
- `party-order-create`（派对下单）
- `delivery-create-address`（新增地址，涉隐私）
- `draw-lottery`（抽奖，有成本/风险）

## 价格单位（再次强调）

- **仅** `calculate-price` 返回「分」（整数，展示 ÷100）。
- 其余订单/餐品金额字段（如 `currentPrice`、`originalPrice`）是「元」字符串，直接展示。
- 积分字段不按金额换算。

## 本作品实际编排用到的真实工具

`now-time-info` · `available-coupons` · `campaign-calendar` · `list-nutrition-foods`（以上用于 `brief` 今日麦麦情报，已实测）；`query-meals` / `calculate-price`（用于省钱引擎真实价格接入点，需门店参数）；其余 30 个工具在标准 Skill 工作流中按场景调用。真实调用记录见 `evidence-real.md`。

## 官方参考

- 接入指南：https://open.mcd.cn/mcp/doc
- 端点：`https://mcp.mcd.cn/mcp-servers/mcd-mcp`
