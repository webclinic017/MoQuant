class MqDailyIndicatorEnum(object):

    def __init__(self, name: str, explain: str):
        self.name = name
        self.explain = explain


total_share = MqDailyIndicatorEnum('total_share', '总股本')
float_share = MqDailyIndicatorEnum('float_share', '流通股本')
free_share = MqDailyIndicatorEnum('float_share', '自由流通股本')
total_mv = MqDailyIndicatorEnum('total_mv', '市值')

extract_from_daily_basic = [total_share, float_share, free_share, total_mv]

open = MqDailyIndicatorEnum('open', '开盘价')
high = MqDailyIndicatorEnum('high', '最高价')
low = MqDailyIndicatorEnum('low', '最低价')
close = MqDailyIndicatorEnum('close', '收盘价')
pre_close = MqDailyIndicatorEnum('pre_close', '上一个交易日收盘价')

extract_from_daily_trade = [open, high, low, close, pre_close]

copy_for_suspend = [total_share, float_share, free_share, total_mv, close]

suspend = MqDailyIndicatorEnum('suspend', '是否停牌')

pe = MqDailyIndicatorEnum('pe', 'PE')
pb = MqDailyIndicatorEnum('pb', 'PB')

dividend_yields = MqDailyIndicatorEnum('dividend_yields', '股息率')

mv_10 = MqDailyIndicatorEnum('mv_10', '10年现金流折现')
mv = MqDailyIndicatorEnum('mv', '永续现金流折现')

grow_score = MqDailyIndicatorEnum('grow_score', '成长评分')
val_score = MqDailyIndicatorEnum('val_score', '价值评分')
