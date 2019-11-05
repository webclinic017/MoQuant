import time

from pandas import DataFrame
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.tsclient import ts_client

log = get_logger(__name__)


def common_fetch_dividend(ts_code: str = None, dt: str = None):
    df: DataFrame = None
    for cnt in range(2):
        log.info('To fetch dividend of stock %s %s' % (ts_code, dt))
        try:
            df = ts_client.fetch_dividend(ts_code=ts_code, ann_date=dt)
            break
        except Exception as e:
            log.error('Calling TuShare too fast. Will sleep 1 minutes...')
            time.sleep(60)

    if df is not None and not df.empty:
        db_client.store_dataframe(df, TsDividend.__tablename__)
        print('Successfully save dividend of stock %s %s' % (ts_code, dt))


def fetch_dividend_by_date(dt: str):
    common_fetch_dividend(dt=dt)


def fetch_dividend_by_code(ts_code: str):
    common_fetch_dividend(ts_code=ts_code)


def init_all_dividend():
    session: Session = db_client.get_session()
    session.query(TsDividend).delete()
    share_list = session.query(MqStockMark).filter(MqStockMark.fetch_data == 1).all()
    for share in share_list:  # type: MqStockMark
        fetch_dividend_by_code(share.ts_code)


if __name__ == '__main__':
    init_all_dividend()
