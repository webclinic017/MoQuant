import sys
import time
from operator import and_

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.utils.cal_basic import get_index_by_ann_date, get_next_index, can_use_next_date
from moquant.utils.datetime import get_current_dt, format_delta, first_report_period, date_max, get_quarter_num

log = get_logger(__name__)


def get_forecast_nprofit_ly(forecast: TsForecast, income_l4: TsIncome):
    forecast_nprofit = None
    if forecast.net_profit_min is not None:
        forecast_nprofit = forecast.net_profit_min * 10000
    elif forecast.net_profit_max is not None:
        forecast_nprofit = forecast.net_profit_max * 10000
    else:
        percent = None
        # choose minimum percent.
        if forecast.p_change_min is not None:
            percent = forecast.p_change_min
        if forecast.p_change_max is not None:
            if percent is None or forecast.p_change_max < percent:
                percent = forecast.p_change_max
        percent = (percent / 100) + 1
        if income_l4 is not None:
            forecast_nprofit = percent * income_l4.n_income_attr_p
        elif forecast.last_parent_net is not None:
            forecast_nprofit = percent * forecast.last_parent_net * 10000
    return forecast_nprofit


def cal_quarter_value(current, last, period: str):
    if period is None:
        return None
    elif int(period[4:6]) == 3:
        return current
    elif current is not None and last is not None:
        return current - last
    else:
        return None


def cal_last_year(current, yoy, adjust):
    """
    (current - x) / abs(x) = yoy
    if x < 0:
    -current/x + 1 = yoy -> x = current / (1- yoy)
    if x >= 0
    current / x - 1 = yoy -> x = current / (yoy + 1)
    """
    if adjust == 0:
        # No adjust, can find in previous fina
        return None
    if current is None or yoy is None:
        return None
    yoy = yoy / 100
    ans1 = current / (1 - yoy) if 1 - yoy != 0 else None
    ans2 = current / (1 + yoy) if 1 + yoy != 0 else None

    if ans1 is None:
        return ans2
    elif ans2 is None:
        return ans1
    elif adjust >= 0:
        return ans1 if ans1 >= ans2 else ans2
    else:
        return ans1 if ans1 < ans2 else ans2


def cal_ltm(current, last_year, last_year_q4, adjust, period):
    if period is None:
        return None
    elif int(period[4:6]) == 12:
        return current
    elif current is None or last_year is None or last_year_q4 is None or adjust is None:
        return None
    else:
        return current + last_year_q4 - last_year + adjust


def get_first_not_none(arr, field_name):
    for item in arr:
        if item is not None and getattr(item, field_name) is not None:
            return getattr(item, field_name)
    return None


def get_min_date(min, arr, index, date_field):
    if index >= len(arr):
        return min
    elif getattr(arr[index], date_field) is None:
        return min
    elif getattr(arr[index], date_field) < min:
        return getattr(arr[index], date_field)
    else:
        return min

def equal_min_date(min, arr, index, date_field):
    if index >= len(arr):
        return False
    elif getattr(arr[index], date_field) == min:
        return True
    else:
        return False

def find_previous_period(arr: list, pos: int, period: str, num: int):
    if num is None:
        return None
    year = int(period[0:4])
    month = int(period[4:6])
    for i in range(num):
        month -= 3
        if month == 0:
            year -= 1
            month = 12
    day = 30 if month == 6 or month == 9 else 31
    to_find_period = '%d%02d%02d' % (year, month, day)
    if pos >= len(arr):
        pos = len(arr) - 1
    while pos >= 0 and arr[pos].end_date != to_find_period and arr[pos].ann_date >= to_find_period:
        pos -= 1
    if pos >= 0 and arr[pos].end_date == to_find_period:
        return arr[pos]
    else:
        return None

def inject_yoy(mq: MqQuarterBasic):
    if mq.revenue is not None and mq.revenue_ly is not None and mq.revenue_ly != 0:
        mq.revenue_yoy = (mq.revenue - mq.revenue_ly) / abs(mq.revenue_ly)

    if mq.quarter_revenue is not None and mq.quarter_revenue_ly is not None and mq.quarter_revenue_ly != 0:
        mq.quarter_revenue_yoy = (mq.quarter_revenue - mq.quarter_revenue_ly) / abs(mq.uarter_revenue_ly)

    if mq.nprofit is not None and mq.nprofit_ly is not None and mq.nprofit_ly != 0:
        mq.nprofit_yoy = (mq.nprofit - mq.nprofit_ly) / abs(mq.nprofit_ly)

    if mq.quarter_nprofit is not None and mq.quarter_nprofit_ly is not None and mq.quarter_nprofit_ly != 0:
        mq.quarter_nprofit_yoy = (mq.quarter_nprofit - mq.quarter_nprofit_ly) / abs(mq.quarter_nprofit_ly)

    if mq.dprofit is not None and mq.dprofit_ly is not None and mq.dprofit_ly != 0:
        mq.dprofit_yoy = (mq.dprofit - mq.dprofit_ly) / abs(mq.dprofit_ly)

    if mq.quarter_dprofit is not None and mq.quarter_dprofit_ly is not None and mq.quarter_dprofit_ly != 0:
        mq.quarter_dprofit_yoy = (mq.quarter_dprofit - mq.quarter_dprofit_ly) / abs(mq.quarter_dprofit_ly)


def inject_dprofit(mq: MqQuarterBasic, fina_arr, fi_i, report_period, income, adjust_income):
    report_quarter = get_quarter_num(report_period)
    dprofit_period = report_period

    nprofit_adjust = None
    if income is not None and income.n_income_attr_p is not None \
        and adjust_income is not None and adjust_income.n_income_attr_p is not None:
        nprofit_adjust = adjust_income.n_income_attr_p - income.n_income_attr_p

    fina: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 0)
    fina_l1: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 1)
    fina_l4: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 4)
    fina_l5: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 5)
    fina_lyy: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, report_quarter)

    dprofit = None
    quarter_dprofit = None
    dprofit_ly = None
    if fina is not None:
        dprofit = fina.profit_dedt
        dprofit_ly = cal_last_year(fina.profit_dedt, fina.dt_netprofit_yoy, nprofit_adjust)
    if dprofit is not None and fina_l1 is not None:
        quarter_dprofit = cal_quarter_value(dprofit, fina_l1.profit_dedt, report_period)

    dprofit_ly_l1 = None
    if fina_l1 is not None:
        dprofit_ly_l1 = cal_last_year(fina_l1.profit_dedt, fina_l1.dt_netprofit_yoy, nprofit_adjust)

    if dprofit_ly is None and fina_l4 is not None:
        dprofit_ly = fina_l4.profit_dedt
    if dprofit_ly_l1 is None and fina_l5 is not None:
        dprofit_ly_l1 = fina_l5.profit_dedt

    quarter_dprofit_ly = None
    if dprofit_ly is not None and dprofit_ly_l1 is not None:
        quarter_dprofit_ly = cal_quarter_value(dprofit_ly, dprofit_ly_l1, report_period)

    adjust = 0
    if dprofit_ly is not None and fina_l4 is not None and fina_l4.profit_dedt is not None:
        adjust = dprofit_ly - fina_l4.profit_dedt

    dprofit_ltm = None
    if fina is not None and fina_lyy is not None:
        dprofit_ltm = cal_ltm(fina.profit_dedt, dprofit_ly, fina_lyy.profit_dedt, adjust,
                              report_period)

    mq.dprofit_period = dprofit_period
    mq.dprofit = dprofit
    mq.dprofit_ly = dprofit_ly

    mq.quarter_dprofit = quarter_dprofit
    mq.quarter_dprofit_ly = quarter_dprofit_ly

    mq.dprofit_ltm = dprofit_ltm



def calculate_adjust(ts_code, share_name, income_arr, i_i, balance_arr, b_i, date, old_income_arr, old_i_i, fina_arr, fi_i) -> MqQuarterBasic:
    report_period = None
    if i_i < len(income_arr) and income_arr[i_i].f_ann_date == date:
        report_period = income_arr[i_i].end_date
    elif b_i < len(balance_arr) and balance_arr[i_i].f_ann_date == date:
        report_period = balance_arr[b_i].end_date

    if report_period == None:
        raise NameError("Can't match adjust report")

    report_quarter = get_quarter_num(report_period)

    balance: TsBalanceSheet = find_previous_period(balance_arr, b_i, report_period, 0)
    nassets = None
    if balance is not None:
        nassets = balance.total_hldr_eqy_exc_min_int

    income : TsIncome = find_previous_period(income_arr, i_i, report_period, 0)
    income_l1: TsIncome = find_previous_period(income_arr, i_i, report_period, 1)
    income_l4: TsIncome = find_previous_period(income_arr, i_i, report_period, 4)
    income_l5: TsIncome = find_previous_period(income_arr, i_i, report_period, 5)
    income_lyy: TsIncome = find_previous_period(income_arr, i_i, report_period, report_quarter)

    # Calculate revenue
    revenue_period = report_period
    revenue = None
    quarter_revenue = None
    if income is not None:
        revenue = income.revenue
    if revenue is not None and income_l1 is not None:
        quarter_revenue = cal_quarter_value(revenue, income_l1.revenue, income.end_date)

    revenue_ly = None
    quarter_revenue_ly = None
    if income_l4 is not None:
        revenue_ly = income_l4.revenue
    if revenue_ly is not None and income_l5 is not None:
        quarter_revenue_ly = cal_quarter_value(revenue, income_l5.revenue, income.end_date)

    # Calculate nprofit
    nprofit_period = report_period
    nprofit = None
    quarter_nprofit = None
    if income is not None:
        nprofit = income.n_income_attr_p
    if nprofit is not None and income_l1 is not None:
        quarter_nprofit = cal_quarter_value(nprofit, income_l1.n_income_attr_p, report_period)

    nprofit_ly = None
    quarter_nprofit_ly = None
    if income_l4 is not None:
        nprofit_ly = income.n_income_attr_p
    if nprofit_ly is not None and income_l5 is not None:
        quarter_nprofit_ly = cal_quarter_value(nprofit_ly, income_l5.n_income_attr_p, report_period)

    nprofit_ltm = None
    if nprofit is not None and income_lyy is not None:
        nprofit_ltm = cal_ltm(nprofit, nprofit_ly, income_lyy.n_income_attr_p, 0, report_period)

    result: MqQuarterBasic = MqQuarterBasic(ts_code=ts_code, share_name=share_name, update_date=date,
                                            report_period=report_period, forecast_period=report_period,
                                            revenue_period=revenue_period, revenue=revenue, revenue_ly=revenue_ly,
                                            quarter_revenue=quarter_revenue, quarter_revenue_ly=quarter_revenue_ly,
                                            nprofit_period=nprofit_period, nprofit=nprofit, nprofit_ly=nprofit_ly,
                                            quarter_nprofit=quarter_nprofit, quarter_nprofit_ly=quarter_nprofit_ly,
                                            nprofit_ltm=nprofit_ltm, nassets=nassets)
    old_income = find_previous_period(old_income_arr, old_i_i, report_period)
    inject_dprofit(result, fina_arr, fi_i, report_period, old_income, income)
    inject_yoy(result)
    return result


def calculate(ts_code, share_name):
    start_time = time.time()
    now_date = get_current_dt()
    session = db_client.get_session()
    last_basic_arr = session.query(MqQuarterBasic).filter(MqQuarterBasic.ts_code == ts_code) \
        .order_by(MqQuarterBasic.update_date.desc()).limit(1).all()
    last_basic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_date = mq_calculate_start_date
    if last_basic is not None:
        from_date = format_delta(last_basic.date, 1)

    # Get all reports including last two year, to calculate ttm
    from_period = first_report_period(from_date, -2)

    income_arr = session.query(TsIncome) \
        .filter(
        and_(TsIncome.ts_code == ts_code, TsIncome.end_date >= from_period, TsIncome.report_type == 1)) \
        .order_by(TsIncome.f_ann_date.asc(), TsIncome.end_date.asc()).all()

    adjust_income_arr = session.query(TsIncome) \
        .filter(
        and_(TsIncome.ts_code == ts_code, TsIncome.end_date >= from_period, TsIncome.report_type == 4)) \
        .order_by(TsIncome.f_ann_date.asc(), TsIncome.end_date.asc()).all()

    balance_arr = session.query(TsBalanceSheet) \
        .filter(and_(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= from_period,
                     TsBalanceSheet.report_type == 1)) \
        .order_by(TsBalanceSheet.f_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    adjust_balance_arr = session.query(TsBalanceSheet) \
        .filter(and_(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= from_period,
                     TsBalanceSheet.report_type == 4)) \
        .order_by(TsBalanceSheet.f_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    fina_arr = session.query(TsFinaIndicator) \
        .filter(and_(TsFinaIndicator.ts_code == ts_code, TsFinaIndicator.end_date >= from_period,
                     TsFinaIndicator.ann_date != None)) \
        .order_by(TsFinaIndicator.ann_date.asc(), TsFinaIndicator.end_date.asc()).all()

    forecast_arr = session.query(TsForecast) \
        .filter(and_(TsForecast.ts_code == ts_code, TsForecast.end_date >= from_period)) \
        .order_by(TsForecast.ann_date.asc(), TsForecast.end_date.asc()).all()

    express_arr = session.query(TsExpress) \
        .filter(and_(TsExpress.ts_code == ts_code, TsExpress.end_date >= from_period)) \
        .order_by(TsExpress.ann_date.asc(), TsExpress.end_date.asc()).all()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    b_i = 0
    ab_i = 0
    i_i = 0
    ai_i = 0
    fi_i = 0
    f_i = 0
    e_i = 0

    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_date <= now_date:
        min_date = format_delta(get_current_dt(), 10)
        min_date = get_min_date(min_date, balance_arr, b_i, 'f_ann_date')
        min_date = get_min_date(min_date, adjust_balance_arr, ab_i, 'f_ann_date')
        min_date = get_min_date(min_date, income_arr, i_i, 'f_ann_date')
        min_date = get_min_date(min_date, adjust_income_arr, ai_i, 'f_ann_date')
        min_date = get_min_date(min_date, fina_arr, fi_i, 'ann_date')
        min_date = get_min_date(min_date, forecast_arr, f_i, 'ann_date')
        min_date = get_min_date(min_date, express_arr, e_i, 'ann_date')

        to_handle_type = None

        if equal_min_date(min_date, adjust_balance_arr, ab_i, 'f_ann_date') or \
                equal_min_date(min_date, adjust_income_arr, ai_i, 'f_ann_date'):
            to_handle_type = 'adjust'
        elif equal_min_date(min_date, balance_arr, b_i, 'f_ann_date') or \
                equal_min_date(min_date, income_arr, i_i, 'f_ann_date') or \
                equal_min_date(min_date, fina_arr, fi_i, 'ann_date'):
            to_handle_type = 'normal'
        elif equal_min_date(min_date, forecast_arr, f_i, 'ann_date') or \
                equal_min_date(min_date, express_arr, e_i, 'ann_date'):
            to_handle_type = 'forecast'

        if to_handle_type == 'adjust':
            session.add(calculate_adjust(ts_code, share_name, adjust_income_arr, ai_i,
                                         adjust_balance_arr, ab_i, min_date,
                                         income_arr, i_i, fina_arr, fi_i))
        elif to_handle_type == 'normal':




        balance: TsBalanceSheet = balance_arr[b_i] if b_i >= 0 else None
        income: TsIncome = income_arr[i_i] if i_i >= 0 else None
        fina: TsFinaIndicator = fina_arr[fi_i] if fi_i >= 0 else None
        forecast: TsForecast = forecast_arr[f_i] if f_i >= 0 else None
        # filter useless forecast
        if forecast is not None and \
                (forecast.p_change_min is None and forecast.p_change_max is None and
                 forecast.net_profit_min is None and forecast.net_profit_max is None):
            forecast = None
        express: TsExpress = express_arr[e_i] if e_i >= 0 else None

        report_period_arr = [report.end_date if report is not None else None
                             for report in [balance, income]]
        report_period = date_max(report_period_arr)
        forecast_period_arr = [report.end_date if report is not None else None
                               for report in [income, forecast, express]]
        forecast_period = date_max(forecast_period_arr)

        quarter_nprofit = None
        quarter_nprofit_ly = None
        nprofit_ltm = None
        quarter_dprofit = None
        quarter_dprofit_ly = None
        dprofit_ltm = None
        quarter_revenue = None
        quarter_revenue_ly = None
        nassets = None

        forecast_quarter = get_quarter_num(forecast_period)
        report_quarter = get_quarter_num(report_period)
        forecast_nprofit = None
        forecast_nprofit_ly = None
        forecast_revenue = None
        forecast_revenue_ly = None
        forecast_nassets = None

        if forecast_period is not None and forecast_period > report_period:
            if express is not None and forecast_period == express.end_date:
                if express.n_income is not None:
                    forecast_nprofit = express.n_income
                if express.revenue is not None:
                    forecast_revenue = express.revenue
                if express.total_hldr_eqy_exc_min_int is not None:
                    forecast_nassets = express.total_hldr_eqy_exc_min_int
                if express.yoy_net_profit is not None:
                    forecast_nprofit_ly = express.yoy_net_profit
                if express.or_last_year is not None:
                    forecast_revenue_ly = express.or_last_year

            if forecast is not None and forecast_period == forecast.end_date:
                income_forecast_ly = find_previous_period(income_arr, i_i, forecast_period, 4)
                forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_forecast_ly)
                if forecast_nprofit is None and forecast_min_nprofit is not None:
                    forecast_nprofit = forecast_min_nprofit
                if forecast_nprofit_ly is None and forecast.last_parent_net is not None:
                    forecast_nprofit_ly = forecast.last_parent_net * 10000

        income_l1: TsIncome = find_previous_period(income_arr, i_i, report_period, 1)
        income_l3: TsIncome = find_previous_period(income_arr, i_i, report_period, 3)
        income_l4: TsIncome = find_previous_period(income_arr, i_i, report_period, 4)
        income_l5: TsIncome = find_previous_period(income_arr, i_i, report_period, 5)
        income_lyy: TsIncome = find_previous_period(income_arr, i_i, report_period, report_quarter)
        income_forecast_lyy: TsIncome = find_previous_period(income_arr, i_i, forecast_period, forecast_quarter)

        adjust_income_l3: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 3)
        adjust_income_l4: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 4)
        adjust_income_l5: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 5)

        fina_l1: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 1)
        fina_l4: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 4)
        fina_l5: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 5)
        fina_lyy: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, report_quarter)

        nprofit_adjust = 0
        # Calculate nprofit
        nprofit_period = None
        nprofit = None
        nprofit_ly = None
        if forecast_nprofit is None:
            # No forecast

        else:
            # forecast
            nprofit_period = forecast_period
            nprofit = forecast_nprofit
            nprofit_ly = forecast_nprofit_ly
            nprofit_ly_l1 = None
            if income is not None:
                quarter_nprofit = cal_quarter_value(forecast_nprofit, income.n_income_attr_p, forecast_period)
            if nprofit_ly is None:
                nprofit_ly = get_first_not_none([adjust_income_l3, income_l3], 'n_income_attr_p')
            if nprofit_ly_l1 is None:
                nprofit_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')

            if nprofit_ly is not None and nprofit_ly_l1 is not None:
                quarter_nprofit_ly = cal_quarter_value(nprofit_ly, nprofit_ly_l1, forecast_period)

            if income_l3 is not None and income_l3.n_income_attr_p is not None:
                nprofit_adjust = nprofit_ly - income_l3.n_income_attr_p

            if income_forecast_lyy is not None:
                nprofit_ltm = cal_ltm(forecast_nprofit, nprofit_ly, income_forecast_lyy.n_income_attr_p, nprofit_adjust,
                                      forecast_period)



        # Calculate revenue
        revenue_period = None
        revenue = None
        revenue_ly = None
        if forecast_revenue is None:

        else:
            # forecast
            revenue_period = report_period
            revenue = forecast_revenue
            revenue_ly = forecast_revenue_ly
            revenue_ly_l1 = None
            if income is not None:
                quarter_revenue = cal_quarter_value(forecast_revenue, income.revenue, forecast_period)

            if revenue_ly is None:
                revenue_ly = get_first_not_none([adjust_income_l3, income_l3], 'revenue')
            if revenue_ly_l1 is None:
                revenue_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'revenue')

            if revenue_ly and revenue_ly_l1 is not None:
                quarter_revenue_ly = cal_quarter_value(revenue_ly, revenue_ly_l1, forecast_period)

        if forecast_nassets is None:
            if balance is not None:
                nassets = balance.total_hldr_eqy_exc_min_int
        else:
            nassets = forecast_nassets



        to_insert = MqQuarterBasic(ts_code=ts_code, share_name=share_name, update_date=from_date,
                                   report_period=report_period, forecast_period=forecast_period,
                                   revenue_period=revenue_period, revenue=revenue, revenue_ly=revenue_ly,
                                   revenue_yoy=revenue_yoy, quarter_revenue=quarter_revenue,
                                   quarter_revenue_ly=quarter_revenue_ly, quarter_revenue_yoy=quarter_revenue_yoy,
                                   nprofit_period=nprofit_period, nprofit=nprofit, nprofit_ly=nprofit_ly,
                                   nprofit_yoy=nprofit_yoy, quarter_nprofit=quarter_nprofit,
                                   quarter_nprofit_ly=quarter_nprofit_ly, quarter_nprofit_yoy=quarter_nprofit_yoy,
                                   nprofit_ltm=nprofit_ltm, dprofit_period=dprofit_period, dprofit=dprofit,
                                   dprofit_ly=dprofit_ly, dprofit_yoy=dprofit_yoy, quarter_dprofit=quarter_dprofit,
                                   quarter_dprofit_ly=quarter_dprofit_ly, quarter_dprofit_yoy=quarter_dprofit_yoy,
                                   dprofit_ltm=dprofit_ltm, nassets=nassets)
        session.add(to_insert)

        from_date = format_delta(from_date, day_num=1)

        if can_use_next_date(balance_arr, 'ann_date', b_i_n, from_date):
            b_i = b_i_n
            b_i_n = get_next_index(balance_arr, 'ann_date', b_i)

        if can_use_next_date(income_arr, 'ann_date', i_i_n, from_date):
            i_i = i_i_n
            i_i_n = get_next_index(income_arr, 'ann_date', i_i)

        if can_use_next_date(adjust_income_arr, 'ann_date', ai_i_n, from_date):
            ai_i = ai_i_n
            ai_i_n = get_next_index(adjust_income_arr, 'ann_date', ai_i)

        if can_use_next_date(fina_arr, 'ann_date', fi_i_n, from_date):
            fi_i = fi_i_n
            fi_i_n = get_next_index(fina_arr, 'ann_date', fi_i)

        if can_use_next_date(forecast_arr, 'ann_date', f_i_n, from_date):
            f_i = f_i_n
            f_i_n = get_next_index(forecast_arr, 'ann_date', f_i)

        if can_use_next_date(express_arr, 'ann_date', e_i_n, from_date):
            e_i = e_i_n
            e_i_n = get_next_index(express_arr, 'ann_date', e_i)

    calculate_time = time.time()
    log.info("Calculate data for %s: %s seconds" % (ts_code, calculate_time - find_index_time))
    session.flush()
    insert_time = time.time()
    log.info("Insert data for %s: %s seconds" % (ts_code, insert_time - calculate_time))


def calculate_all():
    session: Session = db_client.get_session()
    now_date = get_current_dt()
    mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == now_date).all()
    for mq in mq_list:
        calculate(mq.ts_code, mq.share_name)
    session.flush()


def run(ts_code: str):
    if ts_code is not None:
        session: Session = db_client.get_session()
        mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).all()
        for mq in mq_list:
            calculate(mq.ts_code, mq.share_name)
    else:
        calculate_all()


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)
