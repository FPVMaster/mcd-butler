# 麦当劳中国 MCP 工具清单（references/tools.md）

> 官方服务共 **24 个工具**，下方为已确认的工具名与用途。完整 24 个工具及精确入参，**以运行时 `python scripts/mcd_mcp.py list` 返回的 schema 为准**（服务器描述优先于本文档）。

## 已确认工具

| 工具名 | 用途 | 关键入参（以运行时为准） |
|---|---|---|
| `now-time-info` | 获取当前时间信息，便于模型判断时段/日期 | 无 |
| `campaign-calender` | 查询麦当劳中国当月营销活动日历（进行中/往期/未来） | 无 |
| `query-nearby-stores` | 到店自提场景下查询可点餐门店 | `city` / `keyword` 等 |
| `query-meals` | 查询菜单/餐品（按品类、关键词） | 品类、关键词、门店相关 |
| `query-meal-detail` | 单个餐品详情（含营养等信息） | 餐品 id |
| `calculate-price` | 价格试算 | 餐品/数量组合；**返回单位为「分」** |
| `create-order` | 下单（到店自取/得来速/麦乐送） | 门店、餐品、取餐方式等；金额单位为「元」 |
| `query-order` | 查询订单 | 订单号；金额单位为「元」 |
| `available-coupons` | 查询当前可领取的麦麦省优惠券列表 | 无 |
| `auto-bind-coupons` | 一键领取麦麦省所有当前可用券（**写操作**） | 无 |
| `my-coupons` | 查询我可用的优惠券 | 无 |
| `query-my-account` | 查询账户/积分余额 | 无 |
| `mall-points-products` | 浏览积分商城商品 | 无 |
| `mall-product-detail` | 积分商品详情 | 商品 id |
| `mall-create-order` | 积分兑换虚拟券（**写操作**） | 商品、数量 |
| `mall-create-order-physical` | 积分兑换实物（**写操作**） | 商品、数量、收货信息 |
| `delivery-query-addresses` | 查询已保存配送地址 | 无 |
| `delivery-create-address` | 新增配送地址（**写操作，涉隐私**） | 姓名、手机号、详细地址 |

## 写操作红线（必须用户确认）

以下工具会改变外部账户状态或外发隐私数据，**只能在用户明确确认后调用**：

- `auto-bind-coupons`
- `create-order`
- `mall-create-order` / `mall-create-order-physical`
- `delivery-create-address`

## 价格单位（再次强调）

- **仅** `calculate-price` 返回「分」（整数，展示 ÷100）。
- 其余订单/餐品金额字段已是「元」字符串，直接展示。
- 积分字段不按金额换算。

## 官方参考

- 接入指南：https://open.mcd.cn/mcp/doc
- 官方仓库：https://github.com/M-China/mcd-mcp-server
- 端点：`https://mcp.mcd.cn`（Streamable HTTP，协议 2025-06-18）
