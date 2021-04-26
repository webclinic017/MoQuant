import time
from pandas import DataFrame
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.ts_trade_cal import TsTradeCal
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils import date_utils

log = get_logger(__name__)


def fetch_from_date(exchange: str):
    session: Session = db_client.get_session()
    result = session.query(func.max(TsTradeCal.cal_date)).filter(TsTradeCal.exchange == exchange).all()
    session.close()
    from_date = fetch_data_start_date
    if len(result) > 0 and not result[0][0] is None:
        from_date = date_utils.format_delta(result[0][0], day_num=1)
    return from_date


def common_fetch(exchange: str, to_date: str = date_utils.get_current_dt()):
    """
    按交易所获取交易日历
    :param exchange: SSE上交所,SZSE深交所
    :param to_date: 获取截止日期
    :return:
    """
    from_date = fetch_from_date(exchange)
    while from_date < to_date:
        next_date = date_utils.format_delta(from_date, 1000)
        if next_date > to_date:
            next_date = to_date
        for cnt in range(2):
            log.info('To fetch trade calendar %s %s~%s' % (exchange, from_date, to_date))
            try:
                df: DataFrame = ts_client.fetch_trade_cal(exchange=exchange, start_date=from_date, end_date=next_date)
                if not df.empty:
                    db_client.store_dataframe(df, TsTradeCal.__tablename__)
                    log.info('Successfully save trade cal: %s~%s' % (from_date, to_date))
                break
            except Exception as e:
                log.exception('Calling TuShare too fast. Will sleep 1 minutes...', exc_info=e)
                time.sleep(60)
                ts_client.init_token()
        from_date = date_utils.format_delta(to_date, 1)


def fetch(to_date: str = date_utils.get_current_dt()):
    common_fetch('SSE', to_date)
    common_fetch('SZSE', to_date)


if __name__ == '__main__':
    fetch()
