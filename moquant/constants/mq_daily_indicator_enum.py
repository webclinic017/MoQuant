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

grow_score = MqDailyIndicatorEnum('grow_score', '成长评分')
