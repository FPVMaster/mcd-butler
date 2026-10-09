# 真实调用证据（麦当劳中国官方 MCP）

本文件记录本作品对麦当劳中国官方 MCP（`mcd-mcp v1.0.0`）的**真实调用**，证明作品真实接入官方服务，而非空壳封装。

## 1. 服务握手（init）

```
serverInfo: {'name': 'mcd-mcp', 'version': '1.0.0'}
```

## 2. 工具清单（37 个真实工具名，list 命令返回）

```
query-order
query-party-store-session
party-order-create
delivery-query-stores
query-lottery-info
draw-lottery
query-party-store-date
campaign-calendar
query-my-coupons
delivery-query-addresses
query-meal-assistance
query-promotions
query-survey-coupon
mall-product-detail
query-party-city
delivery-create-address
order-list
mall-order-detail
query-party-store
available-coupons
now-time-info
query-nearby-stores
query-my-prizes
mall-order-list
list-nutrition-foods
query-store-coupons
create-order
query-my-account
auto-bind-coupons
calculate-price
cancel-order
query-meals
query-meal-detail
mall-create-order
mall-points-products
```

## 3. 今日麦麦情报（brief 命令真实输出）

```
🍔 麦麦管家 · 今日麦麦情报（真实调用麦当劳中国官方 MCP）
================================================================
🕐 当前时间：2026-10-09 17:36:56（FRIDAY）

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

## 4. 真实官方价省钱引擎（save --budget 60 实跑）

调用链：`query-nearby-stores`（定位门店）→ `query-meals`（119 项真实餐品，含 currentPrice/originalPrice）→ 引擎按官方折扣排序。**价格全部来自官方实时接口，无任何虚构**。

```

🍔 麦麦管家 · 省钱最优解（预算 ¥60.0 · 真实官方价）
📍 门店：麦当劳上海黄浦华旭国际大厦餐厅（南京东路街道西藏中路336号，storeCode=1450713）
----------------------------------------------------------------
【方案 1 · 双人餐】全明星双人分享餐八件套
   官方现价 ¥49.90（原价 ¥114.50，立省 ¥64.60）｜分类：小食拼盘
/多人餐
【方案 2 · 单人餐】人气超值四件套随心选
   官方现价 ¥28.00（原价 ¥57.00，立省 ¥29.00）｜分类：精选单人餐
【方案 3 · 单人餐】安格斯厚牛堡四件套随心选
   官方现价 ¥37.00（原价 ¥66.00，立省 ¥29.00）｜分类：精选单人餐
----------------------------------------------------------------
💡 省额 = 官方原价-现价（实时接口）；再叠加可领券（见 daily/brief）或 App 内券面额，能更省。
```

## 5. 今日最划算日报（daily 命令实跑）

编排 4 个只读工具：`now-time-info` + `campaign-calendar` + `available-coupons` + `query-meals`，输出决策版日报。

```
📰 麦麦管家 · 今日吃什么最划算（真实官方数据）
================================================================
🕐 2026-10-09 17:37:04（FRIDAY）

📅 今日活动：
   · 韩式风味蘸酱上新❤️就「酱」心有所「薯」
   · 麦当劳 X PEACEMINUSONE
   · 麦当劳联动G-DRAGON 

🎟️ 可领券（前 5）：麦旋风任选、巧克力味厚松饼猪柳蛋套餐、巧克力味厚松饼猪柳蛋套餐、巧克力味厚松饼猪柳蛋套餐、巧克力味厚松饼猪柳蛋套餐

💰 今日最划算 Top5（麦当劳上海黄浦华旭国际大厦餐厅 · 南京东路街道西藏中路336号）：
   1. 全明星双人分享餐八件套 —— ¥49.9（原 ¥114.5，省 ¥64.6）
   2. BFF四宫格小食盘双人餐 —— ¥62.9（原 ¥122.5，省 ¥59.6）
   3. 人气超值四件套随心选 —— ¥28.0（原 ¥57.0，省 ¥29.0）
   4. 安格斯厚牛堡四件套随心选 —— ¥37.0（原 ¥66.0，省 ¥29.0）
   5. 麦辣鸡腿堡四件套 —— ¥28.0（原 ¥57.0，省 ¥29.0）

================================================================
💡 数据均来自麦当劳中国官方 MCP 实时返回；下单请以 App 实际结算为准。
```

## 6. 合规说明

- 以上调用均为**只读**（now-time-info / available-coupons / campaign-calendar / list-nutrition-foods / query-nearby-stores / query-meals），未触发任何下单、领券、抽奖、兑换等写操作，不损害账号。
- 验证用 Token 仅用于本次联调，未写入任何仓库文件；参赛/部署时由使用者自行在环境变量 `MCD_MCP_TOKEN` 中配置。
