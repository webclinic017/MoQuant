import time

from pandas import DataFrame
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_sys_param import MqSysParam
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils.datetime import format_delta, get_current_dt

log = get_logger(__name__)

param_key = 'STK_LIMIT_DATE'


def fetch_stk_limit_by_date(dt: str):
    df: DataFrame = None
    for cnt in range(2):
        log.info('To fetch stk limit of %s' % dt)
        try:
            df = ts_client.fetch_stk_limit(trade_date=dt)
            break
        except Exception as e:
            log.error('Calling TuShare too fast. Will sleep 1 minutes...')
            time.sleep(60)

    if df is not None and not df.empty:
        db_client.store_dataframe(df, TsStkLimit.__tablename__)
        print('Successfully save stk limit of %s' % dt)


def update_stk_limit_to(dt: str):
    session: Session = db_client.get_session()
    param_list = session.query(MqSysParam).filter(MqSysParam.param_key == param_key).all()
    param: MqSysParam = None if len(param_list) == 0 else param_list[0]
    if param is None:
        param = MqSysParam(param_key=param_key, param_value=format_delta(fetch_data_start_date, -1))
        session.add(param)
        session.flush()
    now: str = format_delta(param.param_value, 1)

    while now <= dt:
        fetch_stk_limit_by_date(now)
        param.param_value = now
        session.flush()
        now = format_delta(now, 1)


if __name__ == '__main__':
    update_stk_limit_to(get_current_dt())
