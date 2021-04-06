## 回测模型
### 执行顺序
1. context - day_init - 判断交易日。每日开盘前初始化，价格，涨跌停价格，分红送股
2. handler - auction_before_trade - 早盘竞价阶段，可下单。目前唯一可下单时间
3. context - deal_after_morning_auction - 早盘竞价成交
4. context - deal_after_afternoon_auction - 尾盘竞价结束后成交
5. context - day_end - 登记分红送股，跳转下一个交易日