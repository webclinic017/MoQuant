# MoQuant
小打小闹的玩意，希望能整理出一套时候自己的交易模型

## Sys Envs
Key|Value|Desc
|:----:|:----:|:----:|
|TS_TOKEN|token|TuShare需要的token|
|DB_HOST|localhost|mysql host|
|DB_PORT|8803|mysql port|
|MQ_DB_SCHEMA|xxx|所用database|
|DB_USER|root|mysql 用户|
|DB_PWD|password|mysql 密码|
|LOG_FILE_NAME|/your-log-path/xx.log|日志保存路径|
|ECHO_SQL|1|输出Sql
|FORECAST_SAVED_PATH|/your-path/|预报保存位置，其中应该有forecast.html，为Choice导出的预报列表|



## Database - MySql
复制db_info.json.sample至db_info.json, 填你自己的MySQL信息. 

## TuShare
复制ts.json.sample至ts.json。

到https://tushare.pro/注册获取token，本脚本需要至少620积分。

## 回测模型
### 执行顺序
1. context - day_init - 判断交易日。每日开盘前初始化，价格，涨跌停价格，分红送股
2. handler - auction_before_trade - 早盘竞价阶段，可下单。目前唯一可下单时间
3. context - deal_after_morning_auction - 早盘竞价成交
4. context - deal_after_afternoon_auction - 尾盘竞价结束后成交
5. context - day_end - 登记分红送股，跳转下一个交易日