import sys

from pandas import DataFrame, Series
from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.scripts import fetch_data, cal_mq_quarter, cal_mq_daily, cal_grow
from moquant.tsclient import ts_client
from moquant.utils import threadpool
from moquant.utils.datetime import get_current_dt, format_delta

log = get_logger(__name__)


def recal_after_report(ts_code: str, dt: str, period: str):
    session: Session = db_client.get_session()
    basic: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    quarter_list = cal_mq_quarter.calculate(ts_code, basic.share_name, fix_from=period)
    for quarter in quarter_list:  # type: MqQuarterBasic
        session.merge(quarter, True)
    session.flush()
    daily_list = cal_mq_daily.calculate(ts_code, basic.share_name, dt, fix_from=dt)
    new_grow_score = 0
    for daily in daily_list:  # type: MqDailyBasic
        session.merge(daily, True)
        new_grow_score = cal_grow.cal_growing_score(daily)
        basic.grow_score = new_grow_score
    session.flush()


def run(dt: str = get_current_dt()):
    if dt is None:
        dt = get_current_dt()

    if not cal_mq_daily.is_done(dt):
        log.info('Daily calculation is not done. Skip fetching latest')
        return

    session: Session = db_client.get_session()
    # Check new report
    to_check: DataFrame = ts_client.fetch_disclosure_date(format_delta(dt, 1))
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
            # recal_after_report(ts_code=row.ts_code, to_date=dt, period=period)
            threadpool.submit(recal_after_report, ts_code=row.ts_code, to_date=dt, period=period)
        threadpool.join()

    # Check forecast


def clear_report_by_date(dt: str):
    session: Session = db_client.get_session()
    session.query(TsIncome).filter(TsIncome.f_ann_date == format_delta(dt, 1)).delete()
    session.query(TsBalanceSheet).filter(TsBalanceSheet.f_ann_date == format_delta(dt, 1)).delete()
    session.query(TsCashFlow).filter(TsCashFlow.f_ann_date == format_delta(dt, 1)).delete()
    session.query(TsFinaIndicator).filter(TsFinaIndicator.ann_date == format_delta(dt, 1)).delete()


if __name__ == '__main__':
    to_date = sys.argv[1] if len(sys.argv) > 1 else None
    # clear_report_by_date(to_date)
    run(to_date)
