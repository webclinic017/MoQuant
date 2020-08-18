class MqDailyIndicatorEnum(object):

    def __init__(self, name: str, explain: str):
        self.name = name
        self.explain = explain


total_share = MqDailyIndicatorEnum('total_share', '总股本')
close = MqDailyIndicatorEnum('close', '收盘价')
total_mv = MqDailyIndicatorEnum('total_mv', '市值')

extract_from_daily_list = [total_share, close, total_mv]

pe = MqDailyIndicatorEnum('pe', 'PE')
pb = MqDailyIndicatorEnum('pb', 'PB')

dividend_yields = MqDailyIndicatorEnum('dividend_yields', '股息率')

mv_10 = MqDailyIndicatorEnum('mv_10', '10年现金流折现')
mv = MqDailyIndicatorEnum('mv', '永续现金流折现')

grow_score = MqDailyIndicatorEnum('grow_score', '成长评分')
val_score = MqDailyIndicatorEnum('val_score', '价值评分')
