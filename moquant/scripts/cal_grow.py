import sys
from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.utils.datetime import get_current_dt

basic_profit = 1000 * 10000
max_peg = Decimal(0.2)


def cal_growing_score(share: MqQuarterBasic):
    session: Session = db_client.get_session()
    score = 0
    if share.dprofit_pe is None or share.dprofit_pe > 50:
        score = -1
    elif share.quarter_dprofit_yoy is None or share.quarter_dprofit_yoy < 0.5:
        score = -1
    elif share.dprofit_peg is None or share.dprofit_peg > max_peg or share.dprofit_peg < 0:
        score = -1

    if score != -1:
        quarter_list = session.query(MqQuarterBasic).filter(
            and_(MqQuarterBasic.ts_code == share.ts_code, MqQuarterBasic.forecast_period == share.dprofit_period)) \
            .order_by(MqQuarterBasic.update_date.desc()).limit(1).all()
        latest: MqQuarterBasic = quarter_list[0] if len(quarter_list) > 0 else None
        if latest is None:
            score = -1
        elif latest.quarter_dprofit_ly is None or abs(latest.quarter_dprofit_ly) < basic_profit:
            score = -1
        elif latest.quarter_dprofit is None or latest.dprofit_ltm is None or \
                abs(latest.quarter_dprofit / latest.dprofit_ltm < 0.15):
            score = -1

    if score != -1:
        score = (1 - share.dprofit_peg / max_peg) * 100

    return score


def get_growing_score(date: str):
    if date is None:
        date = get_current_dt()
    result: dict = {}
    session: Session = db_client.get_session()
    share_list = session.query(MqDailyBasic).filter(MqDailyBasic.date == date).all()
    for share in share_list:  # type: MqDailyBasic
        result[share.ts_code] = cal_growing_score(share)

    return result


def run(fetch_date: str):
    if fetch_date is None:
        fetch_date = get_current_dt()
    score: dict = get_growing_score(fetch_date)
    session: Session = db_client.get_session()
    share_list = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == fetch_date).all()
    for share in share_list:  # type: MqStockMark
        if share.ts_code in score:
            share.grow_score = score[share.ts_code]
    session.flush()


if __name__ == '__main__':
    run(fetch_date=sys.argv[1] if len(sys.argv) > 1 else None)
