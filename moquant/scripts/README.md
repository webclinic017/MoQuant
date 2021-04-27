# 脚本
- 需要初始化 init_table
- 第一次获取分红数据，可用 fetch_dividend.init_dividend

## 每日拉取数据
总入口 daily.py 拉取顺序
1. fetch_dividend - 获取分红数据
2. fetch_stk_limit - 获取涨跌停价格 (TODO 无涨跌幅限制情况未处理)
3. fetch_trade_cal - 获取交易日历
4. init_ts_basic - 更新股票列表
5. fetch_data - 按股票拉取数据，包括季报、每日数据等
    - 利润表
6. calculate.remove_after_fetch - 步骤5后清除一些需要重算的数据，例如季报延迟，需重算PE等
7. clear_after_fetch, calculate.run - 步骤6后可异步执行，清除可能存在的重复数据（季报），然后进行计算

## 计算
总入口 calculate.run 计算顺序
1. cal_mq_quarter
    - 从季报、预报、快报中获取数据。同一季度优先级为，往年季报修正 > 今年季报 > 快报 > 预报 > 人为预测。区间值取最差情况。需要做到每个日期下，对应每个季度指标都只有一份
    - copy_from_latest 从上一个公布日期补全本季度的基础指标
    - fill_empty 上一步不能copy的，在这填充（分红、预报的归母净利等）
    - cal_quarter_ltm 计算一个LTM值
    - cal_avg 计算平均值，资产类
    - cal_du_pont 杜邦分析。依赖 cal_avg, cal_quarter_ltm
    - cal_rev_pay 应收、应付总和
    - cal_fcf 自由现金流（计算公式待改善）
    - cal_ratio 各种占比。依赖 cal_rev_pay
    - cal_complex_quarter_ltm 复杂指标的LTM。最后的指标
    - cal_risk_point 暴雷预测。最后
    
2. cal_mq_daily
    - extract_from_daily_basic 从接口就能获取的日级基础指标
    - cal_pepb 计算PE、PB，用的是最新的含预测LTM
    - cal_dividend 股息率
    - cal_dcf 自由现金流估值（计算公式待改善）
    - cal_score 打分（有待改善）
    
3. cal_message 目前只有季报类消息