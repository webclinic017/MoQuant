from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_basic import TsBasic
from moquant.scripts import calculate
from moquant.scripts.fetch import fetch_dividend, fetch_trade_cal, fetch_data, clear_after_fetch
from moquant.utils import date_utils, threadpool, env_utils
from moquant.scripts.fetch import init_ts_basic


def do_after_fetch(ts_code: str, to_date: str = date_utils.get_current_dt()):
    clear_after_fetch.clear(ts_code)
    calculate.run(ts_code=ts_code, to_date=to_date)


def run():
    args = env_utils.get_args()
    ts_code = args.code
    to_date = args.date
    parallel = args.parallel
    if to_date is None:
        to_date = date_utils.get_current_dt()

    fetch_trade_cal.fetch(to_date)

    init_ts_basic.init()

    basic_list = []
    session: Session = db_client.get_session()
    if ts_code is not None and ts_code != '':
        basic_list = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
    else:
        basic_list = session.query(TsBasic).all()
    session.close()

    for basic in basic_list:
        r, from_date = fetch_data.fetch_data_by_code(basic.ts_code, to_date)
        if not r:
            continue
        if from_date is not None:
            calculate.remove_after_fetch(ts_code, from_date)
        if parallel == 1:
            threadpool.submit(do_after_fetch, ts_code=basic.ts_code, to_date=to_date)
        else:
            do_after_fetch(ts_code=basic.ts_code, to_date=to_date)

    threadpool.join()
