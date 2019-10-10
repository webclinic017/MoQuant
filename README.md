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
|PASS_FETCH_BASIC|1|跳过获取股票基本信息



## Database - MySql
复制db_info.json.sample至db_info.json, 填你自己的MySQL信息. 

## TuShare
复制ts.json.sample至ts.json。

到https://tushare.pro/注册获取token，本脚本需要至少620积分。