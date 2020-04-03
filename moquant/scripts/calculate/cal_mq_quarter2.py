import time
from decimal import Decimal
from functools import partial

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date, mq_report_type, mq_quarter_indicator_enum
from moquant.dbclient import db_client
from moquant.dbclient.mq_forecast_agg import MqForecastAgg
from moquant.dbclient.mq_quarter_index import MqQuarterIndex
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.service.mq_quarter_store import MqQuarterStore
from moquant.utils.date_utils import format_delta, get_current_dt

log = get_logger(__name__)


def init_quarter_store(ts_code, from_period=mq_calculate_start_date) -> MqQuarterStore:
    store = MqQuarterStore()
    session: Session = db_client.get_session()
    arr = session.query(MqQuarterIndex).filter(MqQuarterIndex.ts_code == ts_code,
                                               MqQuarterIndex.period >= from_period).all()
    for i in arr:
        store.add(i)
    session.close()
    return store


def ready_data(ts_code: str, from_date: str):
    session: Session = db_client.get_session()
    income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.mq_ann_date >= from_date, TsIncome.report_type == 1) \
        .order_by(TsIncome.mq_ann_date.asc(), TsIncome.end_date.asc()).all()

    adjust_income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.mq_ann_date >= from_date, TsIncome.report_type == 4) \
        .order_by(TsIncome.mq_ann_date.asc(), TsIncome.end_date.asc()).all()

    balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.mq_ann_date >= from_date,
                TsBalanceSheet.report_type == 1) \
        .order_by(TsBalanceSheet.mq_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    adjust_balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.mq_ann_date >= from_date,
                TsBalanceSheet.report_type == 4) \
        .order_by(TsBalanceSheet.mq_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    cash_arr = session.query(TsCashFlow) \
        .filter(TsCashFlow.ts_code == ts_code, TsCashFlow.mq_ann_date >= from_date,
                TsCashFlow.report_type == 1) \
        .order_by(TsCashFlow.mq_ann_date.asc(), TsCashFlow.end_date.asc()).all()

    adjust_cash_arr = session.query(TsCashFlow) \
        .filter(TsCashFlow.ts_code == ts_code, TsCashFlow.mq_ann_date >= from_date,
                TsCashFlow.report_type == 4) \
        .order_by(TsCashFlow.mq_ann_date.asc(), TsCashFlow.end_date.asc()).all()

    fina_arr = session.query(TsFinaIndicator) \
        .filter(TsFinaIndicator.ts_code == ts_code, TsFinaIndicator.ann_date >= from_date,
                TsFinaIndicator.ann_date != None) \
        .order_by(TsFinaIndicator.ann_date.asc(), TsFinaIndicator.end_date.asc()).all()

    dividend_arr = session.query(TsDividend) \
        .filter(TsDividend.ts_code == ts_code, TsDividend.ann_date >= from_date) \
        .order_by(TsDividend.ann_date.asc()).all()

    forecast_arr = session.query(MqForecastAgg) \
        .filter(MqForecastAgg.ts_code == ts_code, MqForecastAgg.ann_date >= from_date) \
        .order_by(MqForecastAgg.ann_date.asc(), MqForecastAgg.end_date.asc()).all()

    session.close()
    return income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, cash_arr, adjust_cash_arr, \
           fina_arr, dividend_arr, forecast_arr


def fit_update_date(date: str, arr: list, field_name: str) -> bool:
    if len(arr) == 0:
        return False
    target_date = getattr(arr[0], field_name)
    return target_date is not None and target_date == format_delta(date, 1)


def common_add(result_list: list, store: MqQuarterStore, to_add: MqQuarterIndex):
    store.add(to_add)
    result_list.append(to_add)


def add_nx(ts_code: str, report_type: int, period: str, update_date: str,
           name: str, value: Decimal,
           result_list: list, store: MqQuarterStore, period_set: set):
    exist = store.find_period_latest(ts_code, name, period)
    if exist is not None and exist.update_date == update_date:
        return
    to_add = MqQuarterIndex(ts_code=ts_code, report_type=(1 << report_type), period=period, update_date=update_date,
                            name=name, value=value)
    common_add(result_list, store, to_add)
    period_set.add(period)


def extract_from_forecast(result_list: list, store: MqQuarterStore, period_set: set, forecast: MqForecastAgg):
    call_add_nx = partial(
        add_nx, ts_code=forecast.ts_code, period=forecast.end_date, update_date=format_delta(forecast.ann_date, -1),
        report_type=mq_report_type.forecast,
        store=store, result_list=result_list, period_set=period_set
    )

    for i in mq_quarter_indicator_enum.extract_from_forecast_list:
        call_add_nx(name=i.name, value=getattr(forecast, i.from_name))


def extract_from_income(result_list: list, store: MqQuarterStore, period_set: set, income: TsIncome):
    call_add_nx = partial(
        add_nx, ts_code=income.ts_code, period=income.end_date, update_date=format_delta(income.mq_ann_date, -1),
        report_type=mq_report_type.report if income.report_type == 1 else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_set=period_set
    )
    for i in mq_quarter_indicator_enum.extract_from_income_list:
        call_add_nx(name=i.name, value=getattr(income, i.from_name))


def extract_from_balance(result_list: list, store: MqQuarterStore, period_set: set, bs: TsBalanceSheet):
    call_add_nx = partial(
        add_nx, ts_code=bs.ts_code, period=bs.end_date, update_date=format_delta(bs.mq_ann_date, -1),
        report_type=mq_report_type.report if bs.report_type == 1 else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_set=period_set
    )

    for i in mq_quarter_indicator_enum.extract_from_bs_list:
        call_add_nx(name=i.name, value=getattr(bs, i.from_name))


def extract_from_cash_flow(result_list: list, store: MqQuarterStore, period_set: set, cf: TsCashFlow):
    call_add_nx = partial(
        add_nx, ts_code=cf.ts_code, period=cf.end_date, update_date=format_delta(cf.mq_ann_date, -1),
        report_type=mq_report_type.report if cf.report_type == 1 else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_set=period_set
    )

    for i in mq_quarter_indicator_enum.extract_from_cf_list:
        call_add_nx(name=i.name, value=getattr(cf, i.from_name))


def extract_from_fina_indicator(result_list: list, store: MqQuarterStore, period_set: set, fina: TsFinaIndicator):
    call_add_nx = partial(
        add_nx, ts_code=fina.ts_code, period=fina.end_date, update_date=format_delta(fina.ann_date, -1),
        report_type=mq_report_type.report,
        store=store, result_list=result_list, period_set=period_set
    )

    for i in mq_quarter_indicator_enum.extract_from_fi_list:
        call_add_nx(name=i.name, value=getattr(fina, i.from_name))


def copy_indicator_from_latest(result_list: list, store: MqQuarterStore, period: str, ts_code: str, update_date: str,
                               name: str):
    i = store.find_period_latest(ts_code, name, period)
    if i.update_date == update_date:
        return
    ni = MqQuarterIndex(ts_code=i.ts_code, report_type=i.report_type, period=i.period, update_date=update_date,
                        name=i.name, value=i.value)
    common_add(result_list, store, ni)


def copy_from_latest(result_list: list, store: MqQuarterStore, period_set: set, ts_code: str, update_date: str):
    call_copy = partial(copy_indicator_from_latest, result_list=result_list, store=store,
                        ts_code=ts_code, update_date=update_date)
    period_list = list(period_set).sort()
    for period in period_list:
        for i in mq_quarter_indicator_enum.extract_from_income_list:
            call_copy(period=period, name=i)
        for i in mq_quarter_indicator_enum.extract_from_bs_list:
            call_copy(period=period, name=i)
        for i in mq_quarter_indicator_enum.extract_from_cf_list:
            call_copy(period=period, name=i)
        for i in mq_quarter_indicator_enum.extract_from_fi_list:
            call_copy(period=period, name=i)
        for i in mq_quarter_indicator_enum.extract_from_forecast_list:
            call_copy(period=period, name=i)


def cal_ltm(find: partial, add: partial):
    pass


def cal_peg(result_list: list, store: MqQuarterStore, period: str, ts_code: str, update_date: str):
    pass


def cal_indicator(result_list: list, store: MqQuarterStore, period: str, ts_code: str, update_date: str):
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)


def calculate(ts_code: str, share_name: str, from_date: str = None, to_date: str = get_current_dt()):
    session: Session = db_client.get_session()
    if from_date is None:
        latest: list = session.query(MqQuarterIndex).filter(MqQuarterIndex.ts_code == ts_code) \
            .order_by(MqQuarterIndex.update_date.desc()).limit(1).all()
        if len(latest) > 0:
            from_date = format_delta(latest[0].update_date, 1)
        else:
            from_date = mq_calculate_start_date
    store = init_quarter_store(ts_code, format_delta(from_date, -1000))

    income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, cash_arr, adjust_cash_arr, \
    fina_arr, dividend_arr, forecast_arr = ready_data(ts_code, from_date)

    result_list = []
    while from_date <= to_date:
        period_set = set([])
        #  TODO 调整修正
        if fit_update_date(from_date, adjust_income_arr, 'mq_ann_date'):
            extract_from_income(result_list, store, period_set, adjust_income_arr[0])
        if fit_update_date(from_date, adjust_balance_arr, 'mq_ann_date'):
            extract_from_balance(result_list, store, period_set, adjust_balance_arr[0])
        if fit_update_date(from_date, adjust_cash_arr, 'mq_ann_date'):
            extract_from_cash_flow(result_list, store, period_set, adjust_cash_arr[0])

        # TODO 财报修正
        if fit_update_date(from_date, income_arr, 'mq_ann_date'):
            extract_from_income(result_list, store, period_set, income_arr[0])
        if fit_update_date(from_date, balance_arr, 'mq_ann_date'):
            extract_from_balance(result_list, store, period_set, balance_arr[0])
        if fit_update_date(from_date, cash_arr, 'mq_ann_date'):
            extract_from_cash_flow(result_list, store, period_set, cash_arr[0])
        if fit_update_date(from_date, fina_arr, 'ann_date'):
            extract_from_cash_flow(result_list, store, period_set, fina_arr[0])

        # TODO 预测修正
        if fit_update_date(from_date, forecast_arr, 'ann_date'):
            extract_from_forecast(result_list, store, forecast_arr[0])

        # TODO 人工预测
        copy_from_latest(result_list, store, period_set, ts_code, from_date)
        cal_indicator(result_list, store, period_set, ts_code, from_date)


def calculate_and_insert(ts_code: str, share_name: str):
    result_list = calculate(ts_code, share_name)
    if len(result_list) > 0:
        session: Session = db_client.get_session()
        start = time.time()
        for item in result_list:  # type: MqQuarterBasic
            session.add(item)
        session.flush()
        session.close()
        log.info("Insert mq_quarter_index for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert into mq_quarter_index %s' % ts_code)


def calculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    stock: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    session.close()
    calculate_and_insert(ts_code, stock.share_name)
