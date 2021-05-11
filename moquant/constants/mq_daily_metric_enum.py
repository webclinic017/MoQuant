class MqDailyMetricEnum(object):

    def __init__(self, name: str, explain: str):
        self.name = name
        self.explain = explain


total_share = MqDailyMetricEnum('total_share', '总股本')
float_share = MqDailyMetricEnum('float_share', '流通股本')
free_share = MqDailyMetricEnum('float_share', '自由流通股本')
total_mv = MqDailyMetricEnum('total_mv', '市值')

extract_from_daily_basic = [total_share, float_share, free_share, total_mv]

open = MqDailyMetricEnum('open', '开盘价')
high = MqDailyMetricEnum('high', '最高价')
low = MqDailyMetricEnum('low', '最低价')
close = MqDailyMetricEnum('close', '收盘价')
pre_close = MqDailyMetricEnum('pre_close', '上一个交易日收盘价')

extract_from_daily_trade = [close]

copy_for_suspend = [total_share, float_share, free_share, total_mv, close]

suspend = MqDailyMetricEnum('suspend', '是否停牌')

pe = MqDailyMetricEnum('pe', 'PE')
pb = MqDailyMetricEnum('pb', 'PB')

dividend_yields = MqDailyMetricEnum('dividend_yields', '股息率')

mv_10 = MqDailyMetricEnum('mv_10', '10年现金流折现')
mv = MqDailyMetricEnum('mv', '永续现金流折现')

grow_score = MqDailyMetricEnum('grow_score', '成长评分')
val_score = MqDailyMetricEnum('val_score', '价值评分')
