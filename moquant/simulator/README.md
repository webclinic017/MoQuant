## 回测模型
### 执行顺序 sim_center
1. context - day_init - 判断交易日。每日开盘前初始化
    - __merge_yesterday_buy - 可交易股票更新
    - __update_for_dividend - 分红送股 (TODO 税率待更正)
    - 股票价格除权
    - 资产、现金计算
2. handler - morning_auction - 早盘竞价阶段，可下单
3. context - deal_after_morning_auction - 早盘竞价成交
    - 买价 > 开盘价，成交
    - 卖价 < 开盘价，成交
4. handler - before_trade - 竞价结束到开盘阶段，可下单
5. context - deal_after_afternoon_auction - 尾盘竞价结束后成交
    - 买价 < 日内最高价，成交
    - 卖价 > 日内最低价，成交
6. context - day_end - 交易日结束
    - __update_price_to_close - 更新价格到收盘价
    - 清空卖光的股票
    - 分红登记
    - 清空未成交订单
7. center - daily_record - 记录净值
8. handler - after_trade - 每日结束
9. context - next_day - 进入下一天

### 测试相关
见 [覆盖情况](https://github.com/SYSU-Momojie/MoQuant/blob/master/moquant/simulator/test/README.md)