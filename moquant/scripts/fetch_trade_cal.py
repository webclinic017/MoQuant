from pandas import DataFrame
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.ts_trade_cal import TsTradeCal
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils.datetime import get_current_dt, format_delta

log = get_logger(__name__)


def fetch_from_date():
    session: Session = db_client.get_session()
    result = session.query(func.max(TsTradeCal.cal_date)).all()
    from_date = fetch_data_start_date
    if len(result) > 0 and not result[0][0] is None:
        from_date = format_delta(result[0][0], day_num=1)
    return from_date


def fetch(to_date: str = get_current_dt()):
    from_date = fetch_from_date()
    log.info('Ready to fetch trade cal %s ~ %s' % (from_date, to_date))
    session: Session = db_client.get_session()
    session.query(TsTradeCal).filter(and_(TsTradeCal.cal_date >= from_date, TsTradeCal.cal_date <= to_date)).delete()
    log.info('Delete old trade cal')
    df: DataFrame = ts_client.fetch_trade_cal(start_date=from_date, end_date=to_date)
    if not df.empty:
        db_client.store_dataframe(df, TsTradeCal.__tablename__)
        log.info('Successfully save trade cal: %s~%s' % (from_date, to_date))


if __name__ == '__main__':
    fetch()
