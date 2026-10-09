# 真实调用证据（麦当劳中国官方 MCP）

本文件记录本作品对麦当劳中国官方 MCP（`mcd-mcp v1.0.0`）的**真实调用**，证明作品真实接入官方服务，而非空壳封装。

## 1. 服务握手（init）

```
serverInfo: {'name': 'mcd-mcp', 'version': '1.0.0'}
```

## 2. 工具清单（37 个真实工具名，list 命令返回）

```
query-store-coupons
delivery-query-stores
order-list
now-time-info
list-nutrition-foods
delivery-query-addresses
create-order
calculate-price
query-survey-coupon
query-my-account
query-party-city
auto-bind-coupons
draw-lottery
mall-order-detail
party-order-create
available-coupons
query-order
query-my-prizes
mall-create-order
query-party-store-date
delivery-create-address
query-meal-detail
query-promotions
query-lottery-info
mall-product-detail
query-meals
query-meal-assistance
mall-order-list
query-nearby-stores
cancel-order
query-party-store
campaign-calendar
query-my-coupons
mall-points-products
query-party-store-session
```

## 3. 今日麦麦情报（brief 命令真实输出）

```
🍔 麦麦管家 · 今日麦麦情报（真实调用麦当劳中国官方 MCP）
================================================================
🕐 当前时间：2026-10-09 17:02:48（FRIDAY）

🎟️  今日可领券（前 8 张）：
   · 麦旋风任选（可领取）
   · 巧克力味厚松饼猪柳蛋套餐（可领取）
   · 巧克力味厚松饼猪柳蛋套餐（可领取）
   · 巧克力味厚松饼猪柳蛋套餐（可领取）
   · 巧克力味厚松饼猪柳蛋套餐（可领取）
   · 薯薯任选（可领取）
   · 免费脆薯饼（可领取）
   · 人气麦旋风买一送一（可领取）
   ……共 9 张可领

📅 近期活动（前 5 条）：
   · [2026年10月7日] 超值𝟗.𝟗元早餐两件套陪你开工啦😋
   · [2026年10月8日] 麦当劳 X PEACEMINUSONE
   · [2026年10月8日] 麦咖啡一早现磨🥳元气早餐震撼来袭！
   · [2026年10月9日] 韩式风味蘸酱上新❤️就「酱」心有所「薯」
   · [2026年10月9日] 麦当劳 X PEACEMINUSONE

🥗 低卡轻食推荐（真实热量 Top5）：
   · 无糖可口可乐中杯 —— 0 kcal
   · 无糖可口可乐大杯 —— 0 kcal
   · 无糖可口可乐小杯 —— 0 kcal
   · 纯悦 —— 0 kcal
   · 锡兰红茶 —— 2 kcal

================================================================
💡 以上均来自麦当劳中国官方 MCP 实时返回；下单/领券请在 WorkBuddy 中确认。
```

## 4. 合规说明

- 以上调用均为**只读**：`now-time-info` / `available-coupons` / `campaign-calendar` / `list-nutrition-foods`，未触发任何下单、领券、抽奖、兑换等写操作，不损害账号。
- 验证用 Token 仅用于本次联调，未写入任何仓库文件；参赛/部署时由使用者自行在环境变量 `MCD_MCP_TOKEN` 中配置。
