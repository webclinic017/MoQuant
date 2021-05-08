import time

from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.dbclient.ts_adj_factor import TsAdjFactor
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.dbclient.ts_trade_cal import TsTradeCal
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
        .order_by(MqDailyPrice.trade_date.desc()) \
        .limit(1).all()

    last_trade_date = None

    if len(p) == 0:  # 没有任何记录，需要从上市开始算
        last_trade_date = basic[0].list_date
    else:
        last_trade_date = date_utils.format_delta(p[0].trade_date, 1)

    adj_arr: list = s.query(TsAdjFactor).filter(TsAdjFactor.ts_code == ts_code) \
        .order_by(TsAdjFactor.trade_date.asc()).all()
    price_data_from_date: str = last_trade_date

    trade_arr: list = s.query(TsDailyTradeInfo) \
        .filter(TsDailyTradeInfo.ts_code == ts_code, TsDailyTradeInfo.trade_date >= price_data_from_date) \
        .order_by(TsDailyTradeInfo.trade_date.asc()).all()
    limit_arr: list = s.query(TsStkLimit) \
        .filter(TsStkLimit.ts_code == ts_code, TsStkLimit.trade_date >= price_data_from_date) \
        .order_by(TsStkLimit.trade_date.asc()).all()
    cal_arr: list = s.query(TsTradeCal) \
        .filter(TsTradeCal.cal_date >= price_data_from_date, TsTradeCal.exchange == basic[0].exchange,
                TsTradeCal.is_open == 1) \
        .order_by(TsTradeCal.cal_date.asc()).all()

    s.close()

    if len(cal_arr) == 0:
        log.warn("No trade calendar from %s" % price_data_from_date)
        return

    if len(trade_arr) == 0 and len(limit_arr) == 0:
        log.info("Nothing to insert into %s %s" % (MqDailyPrice.__tablename__, ts_code))
        return

    adj_i = 0
    trade_i = 0
    limit_i = 0
    cal_i = 0
    to_insert = []

    while last_trade_date <= to_date:
        limit_i = find_index_by_date(limit_arr, limit_i, last_trade_date, 'trade_date')
        adj_i = find_index_by_date(adj_arr, adj_i, last_trade_date, 'trade_date')
        trade_i = find_index_by_date(trade_arr, trade_i, last_trade_date, 'trade_date')
        cal_i = find_index_by_date(cal_arr, cal_i, last_trade_date, 'cal_date')

        adj: TsAdjFactor = adj_arr[adj_i]
        t: TsDailyTradeInfo = trade_arr[trade_i]
        l: TsStkLimit = limit_arr[limit_i]
        cal: TsTradeCal = cal_arr[cal_i]

        if cal.cal_date != last_trade_date:
            # 非交易日
            last_trade_date = date_utils.format_delta(last_trade_date, 1)
            continue

        if l.trade_date != last_trade_date:  # 涨跌停价格有可能没有数据
            l = None

        if t.trade_date != last_trade_date:  # 在停牌
            p = MqDailyPrice(ts_code=ts_code, trade_date=last_trade_date, adj=adj.adj_factor, is_trade=0)
        else:
            # 虽然前一天收盘价是前复权的，t-1当天的复权因子 / t的复权因子 * t的复权因子 / 最新的复权因子，所以没有影响
            p = MqDailyPrice(ts_code=ts_code, trade_date=last_trade_date, adj=adj.adj_factor, is_trade=1,
                             open=t.open, close=t.close, high=t.high, low=t.low, pre_close=t.pre_close)
            if l is not None:
                p.up_limit = l.up_limit
                p.down_limit = l.down_limit
            else:
                pass  # TODO 需要的话再自己计算一下涨跌停价格

        to_insert.append(p)
        last_trade_date = date_utils.format_delta(last_trade_date, 1)

    insert_with_msg(ts_code, to_insert)


def insert_with_msg(ts_code: str, to_insert: list):
    """
    插入数据，打印日志
    :param ts_code: 股票编码
    :param to_insert: 插入数据
    :return:
    """
    if len(to_insert) > 0:
        start_time = time.time()
        db_client.batch_insert(to_insert)
        log.info("Insert %s for %s: %s seconds" % (MqDailyPrice.__tablename__, ts_code, time.time() - start_time))
    else:
        log.info('Nothing to insert into %s %s' % (MqDailyPrice.__tablename__, ts_code))


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
                                       MqDailyPrice.trade_date >= from_date).delete()
    session.close()


if __name__ == '__main__':
    calculate_by_code('000001.SZ')
