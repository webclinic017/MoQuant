import decimal

from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.utils import decimal_utils


class SimDailyPrice(object):

    def __init__(self, ts_code: str, trade_date: str, is_trade: int,
                 adj_type: str, adj: decimal, latest_adj: decimal,
                 open_price: decimal, high: decimal, low: decimal, close: decimal,
                 up_limit: decimal, down_limit: decimal, pre_close: decimal):
        factor = 1
        if adj_type == 'qfq' and not decimal_utils.equals(adj, latest_adj):
            factor = decimal_utils.div(adj, latest_adj)
        elif adj_type == 'hfq':
            factor = adj

        self.ts_code = ts_code
        self.trade_date = trade_date
        self.is_trade = is_trade
        self.open = decimal_utils.mul(open_price, factor)
        self.high = decimal_utils.mul(high, factor)
        self.low = decimal_utils.mul(low, factor)
        self.close = decimal_utils.mul(close, factor)
        self.up_limit = decimal_utils.mul(up_limit, factor)
        self.down_limit = decimal_utils.mul(down_limit, factor)
        self.pre_close = decimal_utils.mul(pre_close, factor)


def from_mq_daily_price(mq: MqDailyPrice, adj_type: str, latest_adj: decimal) -> SimDailyPrice:
    """
    转化返回不复权价格
    :param mq: 原始价格数据
    :param adj_type: 复权类型 qfq-前复权 hfq-后复权 其他-不复权
    :param latest_adj: 最新复权因子
    :return:
    """
    return SimDailyPrice(ts_code=mq.ts_code, trade_date=mq.trade_date, is_trade=mq.is_trade,
                         adj_type=adj_type, adj=mq.adj, latest_adj=latest_adj,
                         open_price=mq.open, high=mq.high, low=mq.low, close=mq.close,
                         up_limit=mq.up_limit, down_limit=mq.down_limit, pre_close=mq.pre_close)
