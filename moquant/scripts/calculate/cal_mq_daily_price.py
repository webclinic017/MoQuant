from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.dbclient.ts_adj_factor import TsAdjFactor
from moquant.dbclient.ts_basic import TsBasic
from moquant.log import get_logger
from moquant.utils import date_utils

log = get_logger(__name__)


def find_index_by_date(arr: list, from_i: str, target_date: str) -> int:
    """
    从数组中找到目标日期的下标
    :param arr:
    :param from_i:
    :param target_date:
    :return:
    """


def calculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    """
    按股票计算
    :param ts_code: 股票编码
    :param to_date: 需要计算到的日期
    :return:
    """
    s: Session = db_client.get_session()
    p: list = s.query(MqDailyPrice) \
        .filter(MqDailyPrice.ts_code == ts_code) \
        .order_by(MqDailyPrice.div_date.desc(), MqDailyPrice.trade_date.desc()) \
        .limit(1).all()

    last_div_date = None
    last_trade_date = None
    last_adj = 1

    if len(p) == 0:  # 没有任何记录，需要从上市开始算
        basic: list = s.query(TsBasic).filter(TsBasic.ts_code == ts_code).limit(1).all()
        if len(basic) == 0:
            log.error("No basic info found %s" % ts_code)
            return

        last_div_date = basic[0].list_date
        last_trade_date = basic[0].list_date
    else:
        last_div_date = p[0].div_date
        last_trade_date = p[0].trade_date
        last_adj = p[0].latest_adj

    adj_arr: list = s.query(TsAdjFactor).filter(TsAdjFactor.ts_code == ts_code) \
        .order_by(TsAdjFactor.trade_date.asc()).all()
