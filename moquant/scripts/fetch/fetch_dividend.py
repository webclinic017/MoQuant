import time

from pandas import DataFrame
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils import date_utils

log = get_logger(__name__)


def common_fetch_dividend(ts_code: str = None, dt: str = None):
    target: str = dt if ts_code is None else ts_code
    df: DataFrame = None
    for cnt in range(2):
        log.info('To fetch dividend %s' % target)
        try:
            # https://tushare.pro/document/2?doc_id=103 分红
            df = ts_client.fetch_dividend(ts_code=ts_code, ann_date=dt)
            break
        except Exception as e:
            log.error('Calling TuShare too fast. Will sleep 1 minutes...')
            time.sleep(60)
            ts_client.init_token()

    if df is not None and not df.empty:
        db_client.store_dataframe(df, TsDividend.__tablename__)
        log.info('Successfully save dividend %s' % target)


def fetch_dividend_by_date(dt: str):
    common_fetch_dividend(ts_code=None, dt=dt)


def update_dividend_to(dt: str):
    session: Session = db_client.get_session()
    td: list = session.query(TsDividend).order_by(TsDividend.ann_date.desc()).limit(1).all()
    session.close()

    now: str = fetch_data_start_date if len(td) == 0 else date_utils.format_delta(td[0].ann_date, 1)

    while now <= dt:
        fetch_dividend_by_date(now)
        now = date_utils.format_delta(now, 1)


def init_dividend():
    """
    按股票初始化分红数据
    :return:
    """
    session: Session = db_client.get_session()
    basic_list = session.query(TsBasic).all()
    session.close()
    for basic in basic_list:  # type: TsBasic
        common_fetch_dividend(basic.ts_code)


if __name__ == '__main__':
    init_dividend()
