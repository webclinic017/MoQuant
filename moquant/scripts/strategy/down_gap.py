from sqlalchemy.orm import Session

from moquant.constants import mq_daily_metric_enum
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.dbclient.mq_share_pool import MqSharePool
from moquant.log import get_logger
from moquant.utils import date_utils, decimal_utils

log = get_logger(__name__)

__strategy = 'down_gap'


def run(dt: str, min_mv=5e8, gap_num=2):
    """
    市值 > 500亿
    近一个月向下缺口 >=2
    :param dt: 对应日期
    :param min_mv: 最低市值要求
    :param gap_num: 需要达到多少个缺口
    :return:
    """
    s: Session = db_client.get_session()
    s.query(MqSharePool).filter(MqSharePool.strategy == __strategy, MqSharePool.dt == dt).delete()

    daily_list: list = s.query(MqDailyMetric) \
        .filter(MqDailyMetric.update_date == dt, MqDailyMetric.name == mq_daily_metric_enum.total_mv.name) \
        .all()

    ts_list: list = []
    for daily in daily_list:  # type: MqDailyMetric
        if daily.value >= min_mv:
            ts_list.append(daily.ts_code)

    if len(ts_list) == 0:
        log.error('No company with 50b mv')
        return

    price_list: list = s.query(MqDailyPrice) \
        .filter(MqDailyPrice.ts_code.in_(ts_list), MqDailyPrice.trade_date.between(date_utils.format_delta(dt, -30), dt)) \
        .order_by(MqDailyPrice.ts_code.asc(), MqDailyPrice.trade_date.asc()) \
        .all()

    gap_price: dict = {}
    last_price: dict = {}
    for p in price_list:  # type: MqDailyPrice
        if p.is_trade == 0:
            # 停牌 无交易 不考虑
            continue
        if p.ts_code not in gap_price:
            gap_price[p.ts_code] = []

        gap: list = gap_price[p.ts_code]

        if p.ts_code in last_price:
            # 判断缺口
            lp: MqDailyPrice = last_price[p.ts_code]
            lp_low = decimal_utils.cal_qfq(lp.low, lp.adj, p.adj)
            op = p.open
            if op < lp.low:
                gap.append(lp)

        # 清楚缺口
        to_remove: list = []
        for lg in gap:  # type: MqDailyPrice
            lg_low = decimal_utils.cal_qfq(lg.low, lg.adj, p.adj)
            if p.high > lg_low:
                to_remove.append(lg)

        for r in to_remove:
            gap.remove(r)

        # 替换前一天价格
        last_price[p.ts_code] = p

    to_insert: list = []

    for ts in ts_list:  # type: str
        if ts in gap_price and len(gap_price[ts]) >= gap_num:
            to_insert.append(
                MqSharePool(dt=dt, strategy=__strategy, ts_code=ts)
            )

    db_client.batch_insert(to_insert)
