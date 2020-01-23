from pandas import DataFrame, Series
from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_fetch_latest_record import MqFetchLatestRecord
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.dbclient.ts_trade_cal import TsTradeCal
from moquant.log import get_logger
from moquant.scripts import fetch_data, clear_after_fetch
from moquant.scripts.calculate import cal_mq_daily, recalculate
from moquant.tsclient import ts_client
from moquant.utils import threadpool, env_utils
from moquant.utils.date_utils import get_current_dt

log = get_logger(__name__)


def get_fetch_record(fetch_type: str, dt: str):
    session: Session = db_client.get_session()
    record_arr = session.query(MqFetchLatestRecord).filter(MqFetchLatestRecord.ann_date == dt,
                                                           MqFetchLatestRecord.fetch_type == fetch_type).all()
    session.close()


def check_report(dt: str):
    session: Session = db_client.get_session()
    # Check new report
    to_check: DataFrame = ts_client.fetch_disclosure_date(dt)
    end_date_column: Series = to_check['end_date']
    end_date_column = end_date_column.drop_duplicates().sort_values(ascending=True)
    log.info('%s periods to check in %s' % (len(end_date_column), dt))
    for index, period in end_date_column.items():
        already_codes = session.query(TsIncome.ts_code).filter(
            and_(TsIncome.report_type == 1, TsIncome.end_date == period)).all()
        existed = [already[0] for already in already_codes]
        end_date_to_check = to_check[(~to_check['ts_code'].isin(existed)) & (to_check['end_date'] == period)] \
            .dropna(how='any')
        log.info(end_date_to_check)
        log.info('%s more to fetch for %s' % (len(end_date_to_check), period))
        for index, row in end_date_to_check.iterrows():
            # og.info(row.ts_code)
            fetch_data.fetch_period_report(ts_code=row.ts_code, to_date=dt)
        already_codes = session.query(TsIncome.ts_code).filter(
            and_(TsIncome.report_type == 1, TsIncome.end_date == period)).all()
        existed = [already[0] for already in already_codes]
        success = end_date_to_check[(end_date_to_check['ts_code'].isin(existed)) &
                                    (end_date_to_check['end_date'] == period)] \
            .drop_duplicates(['ts_code', 'end_date'])
        log.info('%s to recalculate for %s' % (len(success), period))
        for index, row in success.iterrows():
            if env_utils.parallel():
                threadpool.submit(recalculate, ts_code=row.ts_code)
            else:
                recalculate(row.ts_code)
        threadpool.join()


def check_forecast(dt: str):
    df: DataFrame = ts_client.fetch_forecast_by_date(dt)
    if df.empty:
        log.info('Not new forecast in %s' % dt)
        return

    record_arr = get_fetch_record('forecast', dt)
    existed_code = set([i.ts_code for i in record_arr])
    dt = dt[~dt['ts_code'].isin(existed_code)]

    db_client.store_dataframe(df, TsForecast.__tablename__)
    for index, data in df.iterrows():
        clear_after_fetch.clear_duplicate_forecast(TsForecast.__tablename__, data['ts_code'])
        recalculate.run(data['ts_code'])


def run():
    dt = get_current_dt()

    if not cal_mq_daily.is_done(dt):
        log.info('Daily calculation is not done. Skip fetching latest')
        return

    dt = get_next_trade_dt(get_current_dt())

    check_report(dt)
    check_forecast(dt)


def get_next_trade_dt(dt: str):
    session: Session = db_client.get_session()
    cal_arr = session.query(TsTradeCal).filter(TsTradeCal.is_open == '1', TsTradeCal.cal_date >= dt) \
        .order_by(TsTradeCal.cal_date.asc()).limit(1).all()
    return cal_arr[0].cal_date
