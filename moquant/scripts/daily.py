from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_basic import TsBasic
from moquant.scripts import calculate, strategy
from moquant.scripts.fetch import fetch_trade_cal, fetch_data, clear_after_fetch, fetch_dividend
from moquant.scripts.fetch import init_ts_basic
from moquant.utils import date_utils, threadpool, env_utils


def fetch_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    r, from_date = fetch_data.fetch_data_by_code(ts_code, to_date)
    if not r:
        return
    if from_date is not None:
        calculate.remove_after_fetch(ts_code, from_date)
    clear_after_fetch.clear(ts_code)
    calculate.run(ts_code=ts_code, to_date=to_date)


def run():
    args = env_utils.get_args()
    ts_code = args.code
    to_date = args.date
    if to_date is None:
        to_date = date_utils.get_current_dt()

    fetch_trade_cal.fetch(to_date)
    fetch_dividend.update_dividend_to(to_date)

    init_ts_basic.init()

    basic_list = []
    session: Session = db_client.get_session()
    if ts_code is not None and ts_code != '':
        basic_list = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
    else:
        basic_list = session.query(TsBasic).all()
    session.close()

    for basic in basic_list:
        if env_utils.parallel():
            threadpool.submit(fetch_by_code, ts_code=basic.ts_code, to_date=to_date)
        else:
            fetch_by_code(ts_code=basic.ts_code, to_date=to_date)

    threadpool.join()

    strategy.generate_strategy_pool(to_date)
