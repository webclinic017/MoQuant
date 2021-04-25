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
|ECHO_SQL|1|输出Sql|


## Database - MySql
复制db_info.json.sample至db_info.json, 填你自己的MySQL信息. 

## TuShare
到 https://tushare.pro/ 注册获取token，本脚本需要至少800积分。

## TODO List
|待完成点|优先级|备注|
|:----:|:----:|:----:|
|相同走势|中|个股跟指数|
|回测框架|低|分红扣税，配股可卖时间|
|回测框架|高|指标缓存|


## 备忘
|注意点|备注|
|:----:|:----:|
|前复权价格不准|复权因子的精度太低了|