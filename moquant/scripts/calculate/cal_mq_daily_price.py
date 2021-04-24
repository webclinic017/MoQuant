from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.dbclient.ts_adj_factor import TsAdjFactor
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.utils import date_utils, decimal_utils

log = get_logger(__name__)


def find_index_by_date(arr: list, from_i: str, target_date: str, date_field: str) -> int:
    """
    从数组中找到目标日期的下标
    :param arr:
    :param from_i:
    :param target_date:
    :return:
    """
    i: str = from_i if from_i >= 0 else 0
    while i < len(arr):
        item_date = getattr(arr[i], date_field)
        if item_date == target_date:
            return i
        i = i + 1
        if i == len(arr) or item_date > target_date:
            break
    return from_i


def need_all_price(adj_arr: list, from_date: str, to_date: str) -> bool:
    """
    检测一下两个日期之间有没有除权，有的话价格需要拉取全部数据
    :param adj_arr: 复权因子列表
    :param from_date: 开始日期
    :param to_date: 结束日期
    :return: 期间有除权
    """
    in_period = False
    for i in range(len(adj_arr)):
        if adj_arr[i].trade_date == from_date:
            in_period = True
        if i > 0 and in_period and not decimal_utils.equals(adj_arr[i].adj_factor, adj_arr[i - 1].adj_factor):
            return True
        if adj_arr[i].trade_date == to_date:
            break
    return False


def calculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    """
    按股票计算
    :param ts_code: 股票编码
    :param to_date: 需要计算到的日期
    :return:
    """
    s: Session = db_client.get_session()

    basic: list = s.query(TsBasic).filter(TsBasic.ts_code == ts_code).limit(1).all()
    if len(basic) == 0:
        log.error("No basic info found %s" % ts_code)
        return

    p: list = s.query(MqDailyPrice) \
        .filter(MqDailyPrice.ts_code == ts_code) \
        .order_by(MqDailyPrice.div_date.desc(), MqDailyPrice.trade_date.desc()) \
        .limit(1).all()

    last_div_date = None
    last_trade_date = None
    last_adj = None

    if len(p) == 0:  # 没有任何记录，需要从上市开始算
        last_div_date = basic[0].list_date
        last_trade_date = basic[0].list_date
        last_adj = 1
    else:
        last_div_date = p[0].div_date
        last_trade_date = date_utils.format_delta(p[0].trade_date, 1)
        last_adj = p[0].latest_adj

    adj_arr: list = s.query(TsAdjFactor).filter(TsAdjFactor.ts_code == ts_code) \
        .order_by(TsAdjFactor.trade_date.asc()).all()
    need_all = need_all_price(adj_arr, last_trade_date, to_date)
    price_data_from_date: str = basic[0].list_date if need_all else last_trade_date

    trade_arr: list = s.query(TsDailyTradeInfo) \
        .filter(TsDailyTradeInfo.ts_code == ts_code, TsDailyTradeInfo.trade_date >= price_data_from_date) \
        .order_by(TsDailyTradeInfo.trade_date.asc()).all()
    limit_arr: list = s.query(TsStkLimit) \
        .filter(TsStkLimit.ts_code == ts_code, TsStkLimit.trade_date >= price_data_from_date) \
        .order_by(TsStkLimit.trade_date.asc()).all()

    s.close()

    adj_i = 0
    trade_i = 0
    limit_i = 0
    to_insert = []

    while last_trade_date <= to_date:
        limit_i = find_index_by_date(limit_arr, limit_i, last_trade_date, 'trade_date')
        adj_i = find_index_by_date(adj_arr, adj_i, last_trade_date, 'trade_date')
        trade_i = find_index_by_date(trade_arr, trade_i, last_trade_date, 'trade_date')

        adj: TsAdjFactor = adj_arr[adj_i]
        t: TsDailyTradeInfo = trade_arr[trade_i]
        l: TsStkLimit = limit_arr[limit_i]

        if l.trade_date != last_trade_date:
            # 非交易日
            last_trade_date = date_utils.format_delta(last_trade_date, 1)
            continue

        is_div: bool = last_trade_date > last_div_date and not decimal_utils.equals(adj.adj_factor, last_adj)
        if not is_div:
            if t.trade_date != last_trade_date:  # 在停牌
                p = MqDailyPrice(ts_code=ts_code, div_date=last_div_date, latest_adj=last_adj,
                                 trade_date=last_trade_date, adj=adj.adj_factor, is_trade=0)
            else:
                # 虽然前一天收盘价是前复权的，t-1当天的复权因子 / t的复权因子 * t的复权因子 / 最新的复权因子，所以没有影响
                p = MqDailyPrice(ts_code=ts_code, div_date=last_div_date, latest_adj=last_adj,
                                 trade_date=last_trade_date, adj=adj.adj_factor, is_trade=1,
                                 open=t.open, close=t.close, high=t.high, low=t.low,
                                 up_limit=l.up_limit, down_limit=l.down_limit,
                                 open_qfq=decimal_utils.cal_qfq(t.open, adj.adj_factor, last_adj),
                                 close_qfq=decimal_utils.cal_qfq(t.close, adj.adj_factor, last_adj),
                                 high_qfq=decimal_utils.cal_qfq(t.high, adj.adj_factor, last_adj),
                                 low_qfq=decimal_utils.cal_qfq(t.low, adj.adj_factor, last_adj),
                                 pre_close_qfq=decimal_utils.cal_qfq(t.pre_close, adj.adj_factor, last_adj),
                                 up_limit_qfq=decimal_utils.cal_qfq(l.up_limit, adj.adj_factor, last_adj),
                                 down_limit_qfq=decimal_utils.cal_qfq(l.down_limit, adj.adj_factor, last_adj))
            to_insert.append(p)
            last_trade_date = date_utils.format_delta(last_trade_date, 1)
        else:
            log.info("batch start insert %d" % len(to_insert))
            db_client.batch_insert(to_insert)
            log.info("batch end insert %d" % len(to_insert))
            to_insert = []
            # 更正一下最新的复权因子，从上市日重新计算
            last_div_date = last_trade_date
            last_adj = adj.adj_factor
            last_trade_date = basic[0].list_date
            adj_i = 0
            trade_i = 0
            limit_i = 0
    db_client.batch_insert(to_insert)


def recalculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    """
    删除相关数据然后重算
    :param ts_code: 股票编码
    :param to_date: 重刷到哪天
    :return:
    """
    session: Session = db_client.get_session()
    session.query(MqDailyPrice).filter(MqDailyPrice.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code, to_date)


def remove_from_date(ts_code: str, from_date: str):
    """
    删除指定日期后的数据
    :param ts_code: 股票编码
    :param from_date: 指定日期
    :return:
    """
    session: Session = db_client.get_session()
    session.query(MqDailyPrice).filter(MqDailyPrice.ts_code == ts_code,
                                       MqDailyPrice.div_date >= from_date).delete()
    session.query(MqDailyPrice).filter(MqDailyPrice.ts_code == ts_code,
                                       MqDailyPrice.trade_date >= from_date).delete()
    session.close()


if __name__ == '__main__':
    calculate_by_code('002762.SZ')
