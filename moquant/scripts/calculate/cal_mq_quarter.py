import sys
import time
from decimal import Decimal
from functools import partial

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date, mq_report_type, mq_quarter_indicator_enum
from moquant.dbclient import db_client, mq_quarter_indicator
from moquant.dbclient.mq_manual_indicator import MqManualIndicator
from moquant.dbclient.mq_quarter_indicator import MqQuarterIndicator
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.scripts import calculate
from moquant.service.mq_quarter_store import MqQuarterStore, init_quarter_store
from moquant.utils import decimal_utils, date_utils

log = get_logger(__name__)


class PeriodObj(object):

    def __init__(self, end_date: str, report_type: int):
        self.end_date = end_date
        self.report_type = report_type


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
        .filter(TsDividend.ts_code == ts_code, TsDividend.ann_date >= from_date, TsDividend.div_proc == '实施') \
        .order_by(TsDividend.ann_date.asc()).all()

    forecast_arr = session.query(TsForecast) \
        .filter(TsForecast.ts_code == ts_code, TsForecast.ann_date >= from_date) \
        .order_by(TsForecast.ann_date.asc(), TsForecast.end_date.asc()).all()

    express_arr = session.query(TsExpress) \
        .filter(TsExpress.ts_code == ts_code, TsExpress.ann_date >= from_date) \
        .order_by(TsExpress.ann_date.asc(), TsExpress.end_date.asc()).all()

    session.close()
    return income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, cash_arr, adjust_cash_arr, \
           fina_arr, dividend_arr, forecast_arr, express_arr


def ready_manual_data(ts_code: str, from_date: str):
    session: Session = db_client.get_session()
    manual_forecast = session.query(MqManualIndicator) \
        .filter(
        MqManualIndicator.ts_code == ts_code, MqManualIndicator.update_date >= from_date,
        MqManualIndicator.report_type == mq_report_type.man_forecast) \
        .order_by(MqManualIndicator.update_date.asc(), MqManualIndicator.period.asc()).all()

    report_fix = session.query(MqManualIndicator) \
        .filter(
        MqManualIndicator.ts_code == ts_code, MqManualIndicator.update_date >= from_date,
        MqManualIndicator.report_type == mq_report_type.report_fix) \
        .order_by(MqManualIndicator.update_date.asc(), MqManualIndicator.period.asc()).all()

    return manual_forecast, report_fix


def fit_update_date(date: str, arr: list, field_name: str) -> bool:
    if len(arr) == 0:
        return False
    target_date = getattr(arr[0], field_name)
    return target_date is not None and target_date == date_utils.format_delta(date, 1)


def common_add(result_list: list, store: MqQuarterStore, to_add: MqQuarterIndicator):
    store.add(to_add)
    result_list.append(to_add)


def common_log_err(ts_code: str, period: str, report_type: int, update_date: str, name: str):
    msg: str = 'Fail to cal %s of %s, period: %s, date: %s' % (name, ts_code, period, update_date)
    if mq_report_type.is_report(report_type):
        # 只对季度报计算不出来报错
        log.error(msg)
    else:
        log.warn(msg)


def add_nx(ts_code: str, report_type: int, period: str, update_date: str,
           name: str, value: Decimal,
           result_list: list, store: MqQuarterStore, period_dict: dict):
    if value is None or name is None:
        return
    exist = store.find_period_latest(ts_code, name, period)
    if exist is not None and exist.update_date == update_date:
        return None
    to_add = MqQuarterIndicator(ts_code=ts_code, report_type=(1 << report_type), period=period, update_date=update_date,
                                name=name, value=value)
    common_add(result_list, store, to_add)
    period_dict[period] = PeriodObj(period, report_type)
    return to_add


def extract_from_express(result_list: list, store: MqQuarterStore, period_dict: dict, express: TsExpress):
    call_add_nx = partial(
        add_nx, ts_code=express.ts_code, period=express.end_date,
        update_date=date_utils.format_delta(express.ann_date, -1),
        report_type=mq_report_type.express,
        store=store, result_list=result_list, period_dict=period_dict
    )

    for i in mq_quarter_indicator_enum.extract_from_express_list:
        call_add_nx(name=i.name, value=getattr(express, i.from_name))


def extract_from_forecast(result_list: list, store: MqQuarterStore, period_dict: dict, forecast: TsForecast):
    update_date = date_utils.format_delta(forecast.ann_date, -1)
    call_add_nx = partial(
        add_nx, ts_code=forecast.ts_code, period=forecast.end_date, update_date=update_date,
        report_type=mq_report_type.forecast,
        store=store, result_list=result_list, period_dict=period_dict
    )

    forecast_nprofit = None
    if forecast.net_profit_min is not None:
        forecast_nprofit = forecast.net_profit_min
    elif forecast.net_profit_max is not None:
        forecast_nprofit = forecast.net_profit_max
    else:
        percent = None
        # choose minimum percent.
        if forecast.p_change_min is not None:
            percent = forecast.p_change_min
        if forecast.p_change_max is not None:
            if percent is None or forecast.p_change_max < percent:
                percent = forecast.p_change_max
        if percent is not None:
            percent = (percent / 100) + 1
            if forecast.last_parent_net is not None:
                forecast_nprofit = percent * forecast.last_parent_net
            else:
                nprofit_ly = store.find_period_latest(forecast.ts_code, mq_quarter_indicator_enum.nprofit.name,
                                                      forecast.end_date, update_date)
                if nprofit_ly is not None and nprofit_ly.value is not None:
                    forecast_nprofit = percent * nprofit_ly.value

    call_add_nx(name=mq_quarter_indicator_enum.nprofit.name, value=forecast_nprofit)


def extract_from_manual(result_list: list, store: MqQuarterStore, period_dict: dict, manual: MqManualIndicator):
    add_nx(ts_code=manual.ts_code, period=manual.period, update_date=date_utils.format_delta(manual.update_date, -1),
           report_type=manual.report_type,
           store=store, result_list=result_list, period_dict=period_dict, name=manual.name, value=manual.value)


def extract_from_income_adjust(result_list: list, store: MqQuarterStore, period_dict: dict, income: TsIncome):
    update_date = date_utils.format_delta(income.mq_ann_date, -1)

    nprofit_new = store.find_period_exact(income.ts_code, mq_quarter_indicator_enum.nprofit.name, income.end_date,
                                          update_date)
    nprofit_old = store.find_period_latest(income.ts_code, mq_quarter_indicator_enum.nprofit.name, income.end_date,
                                           date_utils.format_delta(update_date, -1))
    dprofit_old = store.find_period_latest(income.ts_code, mq_quarter_indicator_enum.dprofit.name, income.end_date,
                                           date_utils.format_delta(update_date, -2))

    to_add = None
    if nprofit_new is None:
        log.error('Cant find nprofit in adjust income. %s %s' % (income.ts_code, income.end_date))
    elif nprofit_old is None or dprofit_old is None:
        to_add = MqQuarterIndicator(ts_code=income.ts_code, report_type=(1 << mq_report_type.report_adjust),
                                    period=income.end_date, update_date=update_date,
                                    name=mq_quarter_indicator_enum.dprofit.name, value=nprofit_new.value)
    else:
        to_add = MqQuarterIndicator(ts_code=income.ts_code, report_type=(1 << mq_report_type.report_adjust),
                                    period=income.end_date, update_date=update_date,
                                    name=mq_quarter_indicator_enum.dprofit.name,
                                    value=decimal_utils.sub(nprofit_new.value,
                                                            decimal_utils.sub(nprofit_old.value, dprofit_old.value)))

    if to_add is not None:
        common_add(result_list, store, to_add)


def extract_from_income(result_list: list, store: MqQuarterStore, period_dict: dict, income: TsIncome):
    call_add_nx = partial(
        add_nx, ts_code=income.ts_code, period=income.end_date,
        update_date=date_utils.format_delta(income.mq_ann_date, -1),
        report_type=mq_report_type.report if income.report_type == '1' else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_dict=period_dict
    )
    for i in mq_quarter_indicator_enum.extract_from_income_list:
        call_add_nx(name=i.name, value=getattr(income, i.from_name))

    # 处理调整 - 净利根据往年调整
    if income.report_type == '4':
        extract_from_income_adjust(result_list, store, period_dict, income)


def extract_from_balance(result_list: list, store: MqQuarterStore, period_dict: dict, bs: TsBalanceSheet):
    call_add_nx = partial(
        add_nx, ts_code=bs.ts_code, period=bs.end_date, update_date=date_utils.format_delta(bs.mq_ann_date, -1),
        report_type=mq_report_type.report if bs.report_type == '1' else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_dict=period_dict
    )

    for i in mq_quarter_indicator_enum.extract_from_bs_list:
        call_add_nx(name=i.name, value=getattr(bs, i.from_name))


def extract_from_cash_flow(result_list: list, store: MqQuarterStore, period_dict: dict, cf: TsCashFlow):
    update_date = date_utils.format_delta(cf.mq_ann_date, -1)
    ts_code = cf.ts_code
    period = cf.end_date
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_add_nx = partial(
        add_nx, ts_code=ts_code, period=period, update_date=update_date,
        report_type=mq_report_type.report if cf.report_type == '1' else mq_report_type.report_adjust,
        store=store, result_list=result_list, period_dict=period_dict
    )

    for i in mq_quarter_indicator_enum.extract_from_cf_list:
        if i.is_cf_h and date_utils.get_quarter_num(cf.end_date) == 3:
            q2: MqManualIndicator = store.find_period_latest(ts_code=cf.ts_code, name=i.name,
                                                             period=date_utils.period_delta(cf.end_date, -1),
                                                             update_date=update_date)
            if q2 is None:
                log.error('Cant find q2 in cash flow %s %s %s' % (cf.ts_code, cf.end_date, cf.mq_ann_date))
                call_add_nx(name=i.name, value=getattr(cf, i.from_name))
            else:
                call_add_nx(name=i.name, value=q2.value)
        else:
            call_add_nx(name=i.name, value=getattr(cf, i.from_name))


def extract_from_fina_indicator(result_list: list, store: MqQuarterStore, period_dict: dict, fina: TsFinaIndicator):
    call_add_nx = partial(
        add_nx, ts_code=fina.ts_code, period=fina.end_date, update_date=date_utils.format_delta(fina.ann_date, -1),
        report_type=mq_report_type.report,
        store=store, result_list=result_list, period_dict=period_dict
    )

    for i in mq_quarter_indicator_enum.extract_from_fi_list:
        call_add_nx(name=i.name, value=getattr(fina, i.from_name))


def extract_from_dividend(result_list: list, store: MqQuarterStore, period_dict: dict, d: TsDividend):
    call_add_nx = partial(
        add_nx, ts_code=d.ts_code, period=d.end_date, update_date=date_utils.format_delta(d.imp_ann_date, -1),
        report_type=mq_report_type.report,
        store=store, result_list=result_list, period_dict=period_dict
    )

    dividend = decimal_utils.mul(d.cash_div_tax, d.base_share)
    call_add_nx(name='dividend', value=dividend)


def copy_indicator_from_latest(result_list: list, store: MqQuarterStore, period: PeriodObj, ts_code: str,
                               update_date: str,
                               name: str, from_name: str = None):
    if from_name is None:
        from_name = name
    i = store.find_period_latest(ts_code, from_name, period.end_date, update_date)
    if i is None or i.update_date == update_date:
        return
    ni = MqQuarterIndicator(ts_code=i.ts_code, report_type=i.report_type, period=i.period, update_date=update_date,
                            name=name, value=i.value)
    common_add(result_list, store, ni)


def copy_from_latest(result_list: list, store: MqQuarterStore, period_dict: dict, ts_code: str, update_date: str):
    call_copy = partial(copy_indicator_from_latest, result_list=result_list, store=store,
                        ts_code=ts_code, update_date=update_date)
    period_list = list(period_dict.keys())
    period_list.sort()
    for period in period_list:
        for i in mq_quarter_indicator_enum.extract_from_income_list:
            call_copy(period=period_dict[period], name=i.name)
        for i in mq_quarter_indicator_enum.extract_from_bs_list:
            call_copy(period=period_dict[period], name=i.name)
        for i in mq_quarter_indicator_enum.extract_from_cf_list:
            call_copy(period=period_dict[period], name=i.name)
        for i in mq_quarter_indicator_enum.extract_from_fi_list:
            call_copy(period=period_dict[period], name=i.name)

        call_copy(period=period_dict[period], name='dividend')


def fill_empty(result_list: list, store: MqQuarterStore, period_dict: dict, ts_code: str, update_date: str):
    period_list = list(period_dict.keys())
    period_list.sort()
    for key in period_list:
        period_o: PeriodObj = period_dict[key]
        period = period_o.end_date
        for i in mq_quarter_indicator_enum.fill_after_copy_fail_list:
            exist = store.find_period_latest(ts_code, i.name, period, update_date)
            if exist is None:
                call_add_nx = partial(
                    add_nx, ts_code=ts_code, period=period, update_date=update_date,
                    store=store, result_list=result_list, period_dict=period_dict,
                    name=i.name
                )
                if i.from_name == '':
                    call_add_nx(report_type=mq_report_type.report, value=Decimal(0))
                else:
                    from_indicator = store.find_period_exact(ts_code, i.from_name, period, update_date)
                    if from_indicator is None or from_indicator.value is None:
                        log.error('Cant find %s to fill %s for %s. Period: %s. Update date: %s' %
                                  (i.from_name, i.name, ts_code, period, update_date))
                    else:
                        add = call_add_nx(report_type=0, value=from_indicator.value)
                        add.report_type = from_indicator.report_type


def cal_quarter_ltm(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    period = period_o.end_date
    report_type = period_o.report_type
    call_find_now = partial(store.find_period_exact, ts_code=ts_code, update_date=update_date)
    call_find_pre = partial(store.find_period_latest, ts_code=ts_code, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)

    for k in mq_quarter_indicator_enum.cal_quarter_list:
        name = k.name
        from_name = k.from_name
        i1 = call_find_now(period=period, name=from_name)
        i2 = call_find_pre(period=date_utils.period_delta(period, -1), name=from_name)
        quarter = mq_quarter_indicator.cal_quarter(name, i1, i2)
        if quarter is None:
            common_log_err(ts_code, period, report_type, update_date, name)
        else:
            call_add(to_add=quarter)

    for k in mq_quarter_indicator_enum.cal_ltm_list:
        name = k.name
        from_name = k.from_name
        i1 = call_find_now(period=period, name=from_name)
        i2 = call_find_pre(period=date_utils.period_delta(period, -1), name=from_name)
        i3 = call_find_pre(period=date_utils.period_delta(period, -2), name=from_name)
        i4 = call_find_pre(period=date_utils.period_delta(period, -3), name=from_name)
        ltm = mq_quarter_indicator.cal_ltm_with_quarter(name, i1, i2, i3, i4)
        if ltm is None:
            common_log_err(ts_code, period, report_type, update_date, name)
        else:
            call_add(to_add=ltm)


def cal_avg(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    period = period_o.end_date
    report_type = period_o.report_type
    call_find_now = partial(store.find_period_exact, ts_code=ts_code, update_date=update_date)
    call_find_pre = partial(store.find_period_latest, ts_code=ts_code)
    call_add = partial(common_add, result_list=result_list, store=store)
    for k in mq_quarter_indicator_enum.cal_avg_list:
        from_name = k.from_name
        i1 = call_find_now(period=period, name=from_name)
        i2 = call_find_pre(period=date_utils.period_delta(period, -1), name=from_name)
        i3 = call_find_pre(period=date_utils.period_delta(period, -2), name=from_name)
        i4 = call_find_pre(period=date_utils.period_delta(period, -3), name=from_name)
        avg = mq_quarter_indicator.cal_ltm_avg(k.name, i1, i2, i3, i4)
        if avg is None:
            common_log_err(ts_code, period, report_type, update_date, k.name)
        else:
            call_add(to_add=avg)


def common_dividend(call_add: partial, call_log: partial, i1: MqQuarterIndicator, i2: MqQuarterIndicator, name: str):
    i = mq_quarter_indicator.dividend(i1, i2, name)
    if i is None:
        call_log(name=name)
    else:
        call_add(to_add=i)
    return i


def common_cal_delta(call_find: partial, call_find_lp: partial, name: str) -> MqQuarterIndicator:
    '''
    计算本期减上期的增量，用于资产等累计值
    '''
    current_period = call_find(name=name)
    last_period = call_find_lp(name=name)
    return mq_quarter_indicator.sub_from('%s_delta' % name, [current_period, last_period])


def cal_du_pont(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    period = period_o.end_date
    report_type = period_o.report_type
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)
    call_log = partial(common_log_err, ts_code=ts_code, period=period, update_date=update_date, report_type=report_type)
    dprofit_ltm = call_find(name='dprofit_ltm')
    revenue_ltm = call_find(name='revenue_ltm')
    nasset_ltm_avg = call_find(name='nassets_ltm_avg')
    total_assets_ltm_avg = call_find(name='total_assets_ltm_avg')

    common_dividend(call_add, call_log, dprofit_ltm, nasset_ltm_avg, 'roe')
    common_dividend(call_add, call_log, dprofit_ltm, revenue_ltm, 'dprofit_margin')
    common_dividend(call_add, call_log, revenue_ltm, total_assets_ltm_avg, 'turnover_rate')
    common_dividend(call_add, call_log, total_assets_ltm_avg, nasset_ltm_avg, 'equity_multiplier')


def cal_ratio(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    '''
    计算一些指标比例，依赖 cal_rev_pay
    '''
    period = period_o.end_date
    report_type = period_o.report_type
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)
    call_log = partial(common_log_err, ts_code=ts_code, period=period, update_date=update_date, report_type=report_type)

    total_receivable = call_find(name='total_receivable')
    revenue = call_find(name='revenue_ltm')
    # 应收风险 = 各种应收总和 / 营业收入
    receive_risk = common_dividend(call_add, call_log, total_receivable, revenue, 'receive_risk')

    total_cur_liab = call_find(name='total_cur_liab')
    total_cur_assets = call_find(name='total_cur_assets')
    # 流动性风险 = 流动负债合计 / 流动资产合计
    liquidity_risk = common_dividend(call_add, call_log, total_cur_liab, total_cur_assets, 'liquidity_risk')

    goodwill = call_find(name='goodwill')
    r_and_d = call_find(name='r_and_d')
    intan_assets = call_find(name='intan_assets')
    total_intangible = mq_quarter_indicator.add_up('total_intangible', [goodwill, r_and_d, intan_assets])
    nassets = call_find(name='nassets')
    oth_eqt_tools_p_shr = call_find(name='oth_eqt_tools_p_shr')
    nassets1 = mq_quarter_indicator.sub_from('nassets1', [nassets, oth_eqt_tools_p_shr])
    # 无形资产风险 = (商誉 + 研发支出 + 无形资产) / (净资产 - 优先股,永续债)
    intangible_risk = common_dividend(call_add, call_log, total_intangible, nassets1, 'intangible_risk')

    money_cap = call_find(name='money_cap')
    oth_cur_assets = call_find(name='oth_cur_assets')
    lt_borr = call_find(name='lt_borr')
    st_borr = call_find(name='st_borr')
    cur = mq_quarter_indicator.add_up('cur', [money_cap, oth_cur_assets])
    borr = mq_quarter_indicator.add_up('borr', [lt_borr, st_borr])
    # 存贷比 = (货币资金 + 其它流动资产) / (短期借款 + 长期借款)
    cash_debt_rate = common_dividend(call_add, call_log, cur, borr, 'cash_debt_rate')

    nprofit_ltm = call_find(name=mq_quarter_indicator_enum.nprofit_ltm.name)
    dividend_ltm = call_find(name=mq_quarter_indicator_enum.dividend_ltm.name)
    # 分红率 = 分红总额LTM / 净利润LTM
    dividend_ratio = common_dividend(call_add, call_log, dividend_ltm, nprofit_ltm,
                                     mq_quarter_indicator_enum.dividend_ratio.name)


def cal_risk_point(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    period = period_o.end_date
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    receive_risk = call_find(name=mq_quarter_indicator_enum.receive_risk.name)
    liquidity_risk = call_find(name=mq_quarter_indicator_enum.liquidity_risk.name)
    intangible_risk = call_find(name=mq_quarter_indicator_enum.intangible_risk.name)

    risk_point = Decimal(0)
    report_type = 0
    if receive_risk is not None:
        report_type = report_type | receive_risk.report_type
        if calculate.gt(receive_risk, 0.5, field='value'):
            risk_point = risk_point + 1

    if liquidity_risk is not None:
        report_type = report_type | liquidity_risk.report_type
        if calculate.gt(liquidity_risk, 0.6, field='value'):
            risk_point = risk_point + 1
    if intangible_risk is not None:
        report_type = report_type | intangible_risk.report_type
        if calculate.gt(intangible_risk, 0.25, field='value'):
            risk_point = risk_point + 1

    to_add = MqQuarterIndicator(ts_code=ts_code, report_type=report_type,
                                period=period, update_date=update_date,
                                name=mq_quarter_indicator_enum.risk_point.name, value=risk_point)
    common_add(result_list, store, to_add)


def cal_rev_pay(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    '''
    计算应收以及应付总和
    '''
    period = period_o.end_date
    report_type = period_o.report_type
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)
    call_log = partial(common_log_err, ts_code=ts_code, period=period, update_date=update_date, report_type=report_type)

    notes_receiv = call_find(name='notes_receiv')
    accounts_receiv = call_find(name='accounts_receiv')
    oth_receiv = call_find(name='oth_receiv')
    lt_rec = call_find(name='lt_rec')
    div_receiv = call_find(name='div_receiv')
    int_receiv = call_find(name='int_receiv')
    total_receivable = mq_quarter_indicator.add_up('total_receivable',
                                                   [notes_receiv, accounts_receiv, lt_rec,
                                                    oth_receiv, div_receiv, int_receiv])
    if total_receivable is None:
        call_log(name='total_receivable')
    else:
        call_add(to_add=total_receivable)

    notes_payable = call_find(name='notes_payable')
    acct_payable = call_find(name='acct_payable')
    total_payable = mq_quarter_indicator.add_up('total_payable', [notes_payable, acct_payable])
    if total_payable is None:
        call_log(name='total_payable')
    else:
        call_add(to_add=total_payable)


def cal_fcf(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    '''
    计算自由现金流，依赖于 cal_rev_pay, cal_quarter_ltm
    '''
    period = period_o.end_date
    report_type = period_o.report_type
    call_find = partial(store.find_period_exact, ts_code=ts_code, period=period, update_date=update_date)
    call_find_ly = partial(store.find_period_latest, ts_code=ts_code, period=date_utils.q4_last_year(period))
    call_find_lp = partial(store.find_period_latest, ts_code=ts_code, period=date_utils.period_delta(period, -1))
    call_add = partial(common_add, result_list=result_list, store=store)
    call_log = partial(common_log_err, ts_code=ts_code, period=period, update_date=update_date, report_type=report_type)

    if mq_report_type.is_report(report_type):
        total_receivable_delta = common_cal_delta(call_find, call_find_ly, 'total_receivable')
        prepayment_delta = common_cal_delta(call_find, call_find_ly, 'prepayment')
        # 经营性应收项目增加 = 应收账款增加 + 预付账款增加 + 应收票据增加
        op_recv_delta = mq_quarter_indicator.add_up('op_recv_delta', [total_receivable_delta, prepayment_delta])

        total_payable_delta = common_cal_delta(call_find, call_find_ly, 'total_payable')
        adv_receipts_delta = common_cal_delta(call_find, call_find_ly, 'adv_receipts')
        # 经营性应付项目增加 = 应付账款增加 + 预收账款增加 + 应付票据增加
        op_pay_delta = mq_quarter_indicator.add_up('op_pay_delta', [total_payable_delta, adv_receipts_delta])

        inventories_delta = common_cal_delta(call_find, call_find_ly, 'inventories')
        lt_amor_exp_delta = common_cal_delta(call_find, call_find_ly, 'lt_amor_exp')

        # 营运资本增加 = 存货增加 + 经营性应收项目增加 + 长期待摊费用增加 - 经营性应付项目增加 - 预提费用增加 (已经取消)
        op_cap_delta = mq_quarter_indicator.sub_from('op_cap_delta', [
            mq_quarter_indicator.add_up('_', [inventories_delta, op_recv_delta, lt_amor_exp_delta]),
            op_pay_delta
        ])

        prov_depr_assets = call_find(name='prov_depr_assets')
        depr_fa_coga_dpba = call_find(name='depr_fa_coga_dpba')
        amort_intang_assets = call_find(name='amort_intang_assets')
        lt_amort_deferred_exp = call_find(name='lt_amort_deferred_exp')
        loss_scr_fa = call_find(name='loss_scr_fa')
        # 折旧与摊销 = 资产减值准备 + 固定资产折旧 + 无形资产摊销 + 长期待摊费用摊销 + 固定资产报废损失
        daa = mq_quarter_indicator.add_up('daa', [prov_depr_assets, depr_fa_coga_dpba, amort_intang_assets,
                                                  lt_amort_deferred_exp, loss_scr_fa])

        # 资本支出 = 非流动性资产增加 - 可供出售金融资产增加
        total_nca_delta = common_cal_delta(call_find, call_find_ly, 'total_nca')
        fa_avail_for_sale_delta = common_cal_delta(call_find, call_find_ly, 'fa_avail_for_sale')
        fa_avail_for_sale_delta = None  # 取消了
        cap_cost = mq_quarter_indicator.sub_from('cap_cost', [total_nca_delta, fa_avail_for_sale_delta])

        dprofit = call_find(name='dprofit')
        # 自由现金流 = 归母扣非净利 + 折旧与摊销 - 营运资本增加 - 资本支出
        fcf = mq_quarter_indicator.sub_from('fcf', [
            mq_quarter_indicator.add_up('_', [dprofit, daa]), op_cap_delta, cap_cost
        ])

    else:
        dprofit_ltm_lp = call_find_lp(name='dprofit_ltm')
        fcf_ltm_lp = call_find_lp(name='fcf_ltm')
        dprofit = call_find(name='dprofit')
        fcf = mq_quarter_indicator.multiply(
            dprofit, mq_quarter_indicator.dividend(fcf_ltm_lp, dprofit_ltm_lp, '_'), 'fcf'
        )

    if fcf is None:
        call_log(name='fcf')
    else:
        call_add(to_add=fcf)


def cal_complex_quarter_ltm(result_list: list, store: MqQuarterStore, period_o: PeriodObj, ts_code: str, update_date: str):
    '''
    计算复杂指标的单季和ltm, 在所有复杂指标计算后
    依赖 cal_fcf
    '''
    period = period_o.end_date
    report_type = period_o.report_type
    call_find_now = partial(store.find_period_exact, ts_code=ts_code, update_date=update_date)
    call_find_pre = partial(store.find_period_latest, ts_code=ts_code, update_date=update_date)
    call_add = partial(common_add, result_list=result_list, store=store)

    for k in mq_quarter_indicator_enum.complex_quarter_list:
        name = k.name
        from_name = k.from_name
        current = call_find_now(period=period, name=from_name)
        lp = call_find_pre(period=date_utils.period_delta(period, -1), name=from_name)
        quarter = mq_quarter_indicator.cal_quarter(name, current, lp)
        if quarter is None:
            common_log_err(ts_code, period, report_type, update_date, name)
        else:
            call_add(to_add=quarter)

    for k in mq_quarter_indicator_enum.complex_ltm_list:
        name = k.name
        from_name = k.from_name
        current = call_find_now(period=period, name=from_name)
        last_year_q4 = call_find_pre(period=date_utils.q4_last_year(period), name=from_name)
        last_year = call_find_pre(period=date_utils.period_delta(period, -4), name=from_name)
        ltm = mq_quarter_indicator.cal_ltm_with_period(name, current, last_year_q4, last_year)
        if ltm is None:
            common_log_err(ts_code, period, report_type, update_date, name)
        else:
            call_add(to_add=ltm)


def cal_indicator(result_list: list, store: MqQuarterStore, period: PeriodObj, ts_code: str, update_date: str):
    cal_quarter_ltm(result_list, store, period, ts_code, update_date)
    cal_avg(result_list, store, period, ts_code, update_date)
    cal_du_pont(result_list, store, period, ts_code, update_date)
    cal_rev_pay(result_list, store, period, ts_code, update_date)
    cal_fcf(result_list, store, period, ts_code, update_date)
    cal_ratio(result_list, store, period, ts_code, update_date)
    cal_complex_quarter_ltm(result_list, store, period, ts_code, update_date)
    cal_risk_point(result_list, store, period, ts_code, update_date)


def cal_complex(result_list: list, store: MqQuarterStore, period_dict: dict, ts_code: str, update_date: str):
    period_list = list(period_dict.keys())
    period_list.sort()
    for key in period_list:
        cal_indicator(result_list, store, period_dict[key], ts_code, update_date)


def cal_inc_rate(n: MqQuarterIndicator, l: MqQuarterIndicator):
    if n is None or l is None:
        return None
    else:
        if mq_quarter_indicator_enum.is_percent_indicator(n.name):
            return decimal_utils.sub(n.value, l.value)
        else:
            return decimal_utils.yoy(n.value, l.value)


def cal_yoy_mom(result_list: list, store: MqQuarterStore):
    for i in result_list:  # type: MqQuarterIndicator
        lm = store.find_period_latest(i.ts_code, i.name, date_utils.period_delta(i.period, -1))
        i.mom = cal_inc_rate(i, lm)
        ly = store.find_period_latest(i.ts_code, i.name, date_utils.period_delta(i.period, -4))
        i.yoy = cal_inc_rate(i, ly)


def calculate_one(ts_code: str, share_name: str, from_date: str = None, to_date=date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    if from_date is None:
        latest: list = session.query(MqQuarterIndicator).filter(MqQuarterIndicator.ts_code == ts_code) \
            .order_by(MqQuarterIndicator.update_date.desc()).limit(1).all()
        if len(latest) > 0:
            from_date = date_utils.format_delta(latest[0].update_date, 1)
        else:
            from_date = mq_calculate_start_date
    store = init_quarter_store(ts_code, date_utils.format_delta(from_date, -1000))

    income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, cash_arr, adjust_cash_arr, \
    fina_arr, dividend_arr, forecast_arr, express_arr = ready_data(ts_code, date_utils.format_delta(from_date, 1))

    manual_forecast, report_fix = ready_manual_data(ts_code, from_date)

    result_list = []
    while from_date <= to_date:
        period_dict: dict = {}

        #  TODO 调整修正
        while fit_update_date(from_date, adjust_income_arr, 'mq_ann_date'):
            extract_from_income(result_list, store, period_dict, adjust_income_arr.pop(0))
        while fit_update_date(from_date, adjust_balance_arr, 'mq_ann_date'):
            extract_from_balance(result_list, store, period_dict, adjust_balance_arr.pop(0))
        while fit_update_date(from_date, adjust_cash_arr, 'mq_ann_date'):
            extract_from_cash_flow(result_list, store, period_dict, adjust_cash_arr.pop(0))
        while fit_update_date(from_date, dividend_arr, 'imp_ann_date'):
            extract_from_dividend(result_list, store, period_dict, dividend_arr.pop(0))

        while fit_update_date(from_date, report_fix, 'update_date'):
            extract_from_manual(result_list, store, period_dict, report_fix.pop(0))
        while fit_update_date(from_date, income_arr, 'mq_ann_date'):
            extract_from_income(result_list, store, period_dict, income_arr.pop(0))
        while fit_update_date(from_date, balance_arr, 'mq_ann_date'):
            extract_from_balance(result_list, store, period_dict, balance_arr.pop(0))
        while fit_update_date(from_date, cash_arr, 'mq_ann_date'):
            extract_from_cash_flow(result_list, store, period_dict, cash_arr.pop(0))
        while fit_update_date(from_date, fina_arr, 'ann_date'):
            extract_from_fina_indicator(result_list, store, period_dict, fina_arr.pop(0))

        # TODO 预测修正
        while fit_update_date(from_date, express_arr, 'ann_date'):
            extract_from_express(result_list, store, period_dict, express_arr.pop(0))
        while fit_update_date(from_date, forecast_arr, 'ann_date'):
            extract_from_forecast(result_list, store, period_dict, forecast_arr.pop(0))

        while fit_update_date(from_date, manual_forecast, 'update_date'):
            extract_from_manual(result_list, store, period_dict, manual_forecast.pop(0))

        if len(period_dict) > 0:
            copy_from_latest(result_list, store, period_dict, ts_code, from_date)
            fill_empty(result_list, store, period_dict, ts_code, from_date)
            cal_complex(result_list, store, period_dict, ts_code, from_date)

        from_date = date_utils.format_delta(from_date, 1)

    cal_yoy_mom(result_list, store)
    return result_list


def calculate_and_insert(ts_code: str, share_name: str, to_date=date_utils.get_current_dt()):
    result_list = calculate_one(ts_code, share_name, to_date=to_date)
    if len(result_list) > 0:
        session: Session = db_client.get_session()
        start = time.time()
        for item in result_list:  # type: MqQuarterBasic
            session.add(item)
        session.flush()
        session.close()
        log.info("Insert mq_quarter_indicator for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert into mq_quarter_indicator %s' % ts_code)


def calculate_by_code(ts_code: str, to_date=date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    basic: TsBasic = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).one()
    session.close()
    if basic is None:
        log.error("Cant find ts_basic of %s" % ts_code)
        return
    calculate_and_insert(ts_code, basic.name, to_date)


def recalculate_by_code(ts_code: str, to_date=date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    session.query(MqQuarterIndicator).filter(MqQuarterIndicator.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code, to_date)


def remove_from_date(ts_code: str, from_date: str):
    session: Session = db_client.get_session()
    session.query(MqQuarterIndicator).filter(MqQuarterIndicator.ts_code == ts_code,
                                             MqQuarterIndicator.update_date >= from_date).delete()
    session.close()


if __name__ == '__main__':
    calculate_by_code(sys.argv[1])
