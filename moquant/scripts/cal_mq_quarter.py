import sys
import time
from operator import and_

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_period
from moquant.dbclient import db_client
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.utils.datetime import get_current_dt, format_delta, get_quarter_num, \
    next_period, period_delta, get_period

log = get_logger(__name__)


def get_index_by_end_date(arr, current_date: str, from_index: int = 0) -> int:
    i = from_index
    while i + 1 < len(arr):
        if arr[i + 1].end_date > current_date:
            break
        else:
            i += 1
    return i


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
        if percent is not None:
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


def same_period(arr, i: int, period: str) -> bool:
    return 0 <= i < len(arr) and arr[i].end_date == period


def calculate_period(ts_code, share_name,
                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                     i_i, ai_i, b_i, ab_i, fi_i,
                     report_period, forecast_period,
                     forecast_nprofit, forecast_nprofit_ly, forecast_revenue, forecast_revenue_ly, forecast_nassets,
                     f_ann_date
                     ):
    report_quarter = get_quarter_num(report_period)
    forecast_quarter = get_quarter_num(forecast_period)

    income: TsIncome = find_previous_period(income_arr, i_i, report_period, 0)
    income_l1: TsIncome = find_previous_period(income_arr, i_i, report_period, 1)
    income_l3: TsIncome = find_previous_period(income_arr, i_i, report_period, 3)
    income_l4: TsIncome = find_previous_period(income_arr, i_i, report_period, 4)
    income_l5: TsIncome = find_previous_period(income_arr, i_i, report_period, 5)
    income_lyy: TsIncome = find_previous_period(income_arr, i_i, report_period, report_quarter)
    income_forecast_lyy: TsIncome = find_previous_period(income_arr, i_i, forecast_period, forecast_quarter)

    balance: TsBalanceSheet = find_previous_period(balance_arr, b_i, report_period, 0)

    adjust_income_l3: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 3)
    adjust_income_l4: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 4)
    adjust_income_l5: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 5)

    fina: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 0)
    fina_l1: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 1)
    fina_l3: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 3)
    fina_l4: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 4)
    fina_l5: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 5)
    fina_lyy: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, report_quarter)

    nprofit_period = None
    nprofit = None
    nprofit_ly = None
    quarter_nprofit = None
    quarter_nprofit_ly = None
    nprofit_adjust = 0
    nprofit_ltm = None
    # Calculate nprofit
    if forecast_nprofit is None:
        # No forecast
        nprofit_period = report_period
        if income is not None:
            nprofit = income.n_income_attr_p
        if nprofit is not None and income_l1 is not None:
            quarter_nprofit = cal_quarter_value(nprofit, income_l1.n_income_attr_p, report_period)

        nprofit_ly = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')
        nprofit_ly_l1 = get_first_not_none([adjust_income_l5, income_l5], 'n_income_attr_p')

        if nprofit_ly is not None and nprofit_ly_l1 is not None:
            quarter_nprofit_ly = cal_quarter_value(nprofit_ly, nprofit_ly_l1, report_period)

        if income_l4 is not None and income_l4.n_income_attr_p is not None:
            nprofit_adjust = nprofit_ly - income_l4.n_income_attr_p

        if nprofit is not None and income_lyy is not None:
            nprofit_ltm = cal_ltm(nprofit, nprofit_ly, income_lyy.n_income_attr_p, nprofit_adjust, report_period)
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

    dprofit_period = None
    dprofit = None
    dprofit_ly = None
    quarter_dprofit = None
    quarter_dprofit_ly = None
    dprofit_ltm = None
    # Calculate dprofit
    if forecast_nprofit is None:
        # No forecast
        dprofit_period = report_period
        if fina is not None:
            dprofit = fina.profit_dedt
        if dprofit is not None and fina_l1 is not None:
            quarter_dprofit = cal_quarter_value(dprofit, fina_l1.profit_dedt, report_period)
        dprofit_ly_l1 = None

        if fina is not None:
            dprofit_ly = cal_last_year(fina.profit_dedt, fina.dt_netprofit_yoy, nprofit_adjust)
        if fina_l1 is not None:
            dprofit_ly_l1 = cal_last_year(fina_l1.profit_dedt, fina_l1.dt_netprofit_yoy, nprofit_adjust)

        if dprofit_ly is None and fina_l4 is not None:
            dprofit_ly = fina_l4.profit_dedt

        if dprofit_ly_l1 is None and fina_l5 is not None:
            dprofit_ly_l1 = fina_l5.profit_dedt

        if dprofit_ly is not None and dprofit_ly_l1 is not None:
            quarter_dprofit_ly = cal_quarter_value(dprofit_ly, dprofit_ly_l1, report_period)

        adjust = 0
        if dprofit_ly is not None and fina_l4 is not None and fina_l4.profit_dedt is not None:
            adjust = dprofit_ly - fina_l4.profit_dedt

        if fina is not None and fina_lyy is not None:
            dprofit_ltm = cal_ltm(fina.profit_dedt, dprofit_ly, fina_lyy.profit_dedt, adjust,
                                  report_period)
    else:
        # Forecast dprofit
        dprofit_period = forecast_period
        dprofit = forecast_nprofit
        if fina is not None and income is not None\
                and income.n_income_attr_p is not None and fina.profit_dedt is not None:
            dprofit = dprofit - (income.n_income_attr_p - fina.profit_dedt)
        dprofit_ly_l1 = None
        if fina is not None:
            quarter_dprofit = cal_quarter_value(dprofit, fina.profit_dedt, forecast_period)
        if dprofit_ly is None:
            dprofit_ly = get_first_not_none([fina_l3], 'profit_dedt')
        if dprofit_ly_l1 is None:
            dprofit_ly_l1 = get_first_not_none([fina_l4], 'profit_dedt')

        if dprofit_ly_l1 is not None and dprofit_ly_l1 is not None:
            quarter_dprofit_ly = cal_quarter_value(dprofit_ly, dprofit_ly_l1, forecast_period)

        if fina_lyy is not None and dprofit_ly is not None:
            dprofit_ltm = cal_ltm(dprofit, dprofit_ly, fina_lyy.profit_dedt, 0, forecast_period)


    # Calculate revenue
    revenue_period = None
    revenue = None
    revenue_ly = None
    quarter_revenue = None
    quarter_revenue_ly = None
    if forecast_revenue is None:
        # No forecast
        revenue_period = report_period
        if income is not None:
            revenue = income.revenue
        if revenue is not None and income_l1 is not None:
            quarter_revenue = cal_quarter_value(revenue, income_l1.revenue, income.end_date)

        revenue_ly = get_first_not_none([adjust_income_l4, income_l4], 'revenue')
        revenue_ly_l1 = get_first_not_none([adjust_income_l5, income_l5], 'revenue')

        if revenue_ly is not None and revenue_ly_l1 is not None:
            quarter_revenue_ly = cal_quarter_value(revenue_ly, revenue_ly_l1, report_period)
    else:
        # forecast
        revenue_period = forecast_period
        revenue = forecast_revenue
        revenue_ly = forecast_revenue_ly
        revenue_ly_l1 = None
        if income is not None:
            quarter_revenue = cal_quarter_value(forecast_revenue, income.revenue, forecast_period)

        if revenue_ly is None:
            revenue_ly = get_first_not_none([adjust_income_l3, income_l3], 'revenue')
        if revenue_ly_l1 is None:
            revenue_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'revenue')

        if revenue_ly is not None and revenue_ly_l1 is not None:
            quarter_revenue_ly = cal_quarter_value(revenue_ly, revenue_ly_l1, forecast_period)

    nassets = None
    if forecast_nassets is None:
        if balance is not None:
            nassets = balance.total_hldr_eqy_exc_min_int
    else:
        nassets = forecast_nassets

    revenue_yoy = None
    if revenue is not None and revenue_ly is not None and revenue_ly != 0:
        revenue_yoy = (revenue - revenue_ly) / abs(revenue_ly)

    nprofit_yoy = None
    if nprofit is not None and nprofit_ly is not None and nprofit_ly != 0:
        nprofit_yoy = (nprofit - nprofit_ly) / abs(nprofit_ly)

    dprofit_yoy = None
    if dprofit is not None and dprofit_ly is not None and dprofit_ly != 0:
        dprofit_yoy = (dprofit - dprofit_ly) / abs(dprofit_ly)

    quarter_revenue_yoy = None
    if quarter_revenue is not None and quarter_revenue_ly is not None and quarter_revenue_ly != 0:
        quarter_revenue_yoy = (quarter_revenue - quarter_revenue_ly) / abs(quarter_revenue_ly)

    quarter_nprofit_yoy = None
    if quarter_nprofit is not None and quarter_nprofit_ly is not None and quarter_nprofit_ly != 0:
        quarter_nprofit_yoy = (quarter_nprofit - quarter_nprofit_ly) / abs(quarter_nprofit_ly)

    quarter_dprofit_yoy = None
    if quarter_dprofit is not None and quarter_dprofit_ly is not None and quarter_dprofit_ly != 0:
        quarter_dprofit_yoy = (quarter_dprofit - quarter_dprofit_ly) / abs(quarter_dprofit_ly)

    return MqQuarterBasic(ts_code=ts_code, share_name=share_name, update_date=format_delta(f_ann_date, -1),
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


def calculate(ts_code, share_name):
    start_time = time.time()
    now_date = get_current_dt()
    max_period = get_period(int(now_date[0:4]), 12)
    forcast_update_date = '20010101'

    session = db_client.get_session()
    last_basic_arr = session.query(MqQuarterBasic).filter(MqQuarterBasic.ts_code == ts_code) \
        .order_by(MqQuarterBasic.update_date.desc()).limit(1).all()
    last_basic: MqQuarterBasic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_period = mq_calculate_start_period
    if last_basic is not None:
        from_period = next_period(last_basic.report_period)
        if last_basic.report_period < last_basic.forecast_period:
            forcast_update_date = format_delta(last_basic.update_date, 1)


    # Get all reports including last two year, to calculate ttm
    period_to_get = period_delta(from_period, -12)

    income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.end_date >= period_to_get, TsIncome.report_type == 1) \
        .order_by(TsIncome.f_ann_date.asc(), TsIncome.end_date.asc()).all()

    adjust_income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.end_date >= period_to_get, TsIncome.report_type == 4) \
        .order_by(TsIncome.f_ann_date.asc(), TsIncome.end_date.asc()).all()

    balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= period_to_get,
                     TsBalanceSheet.report_type == 1) \
        .order_by(TsBalanceSheet.f_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    adjust_balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= period_to_get,
                     TsBalanceSheet.report_type == 4) \
        .order_by(TsBalanceSheet.f_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    fina_arr = session.query(TsFinaIndicator) \
        .filter(TsFinaIndicator.ts_code == ts_code, TsFinaIndicator.end_date >= period_to_get,
                     TsFinaIndicator.ann_date != None) \
        .order_by(TsFinaIndicator.ann_date.asc(), TsFinaIndicator.end_date.asc()).all()

    forecast_arr = session.query(TsForecast) \
        .filter(and_(TsForecast.ts_code == ts_code, TsForecast.end_date >= period_to_get)) \
        .order_by(TsForecast.ann_date.asc(), TsForecast.end_date.asc()).all()

    express_arr = session.query(TsExpress) \
        .filter(and_(TsExpress.ts_code == ts_code, TsExpress.end_date >= period_to_get)) \
        .order_by(TsExpress.ann_date.asc(), TsExpress.end_date.asc()).all()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    b_i = get_index_by_end_date(balance_arr, from_period)
    ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -4))
    i_i = get_index_by_end_date(income_arr, from_period)
    ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -4))
    fi_i = get_index_by_end_date(fina_arr, from_period)
    f_i = get_index_by_end_date(forecast_arr, from_period)
    e_i = get_index_by_end_date(express_arr, from_period)

    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_period <= max_period:
        report_period = None
        forecast_period = None
        forecast_nprofit = None
        forecast_revenue = None
        forecast_nassets = None
        forecast_nprofit_ly = None
        forecast_revenue_ly = None

        if same_period(forecast_arr, f_i, from_period):
            forecast: TsForecast = forecast_arr[f_i]
            if forcast_update_date != forecast.ann_date:
                report_period = period_delta(from_period, -1)
                forecast_period = from_period
                income_forecast_ly = find_previous_period(income_arr, i_i, forecast_period, 4)
                forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_forecast_ly)
                if forecast_nprofit is None and forecast_min_nprofit is not None:
                    forecast_nprofit = forecast_min_nprofit
                if forecast_nprofit_ly is None and forecast.last_parent_net is not None:
                    forecast_nprofit_ly = forecast.last_parent_net * 10000
                session.add(
                    calculate_period(ts_code, share_name,
                                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                     i_i, ai_i, b_i, ab_i, fi_i,
                                     report_period, forecast_period,
                                     forecast_nprofit, forecast_nprofit_ly, forecast_revenue, forecast_revenue_ly,
                                     forecast_nassets,
                                     forecast.ann_date)
                )
            f_i = f_i + 1
        elif same_period(express_arr, e_i, from_period):
            express: TsExpress = express_arr[e_i]
            if forcast_update_date != express.ann_date:
                report_period = period_delta(from_period, -1)
                forecast_period = from_period
                forecast_nprofit = express.n_income
                forecast_revenue = express.revenue
                forecast_nassets = express.total_hldr_eqy_exc_min_int
                forecast_nprofit_ly = express.yoy_net_profit
                forecast_revenue_ly = express.or_last_year
                session.add(
                    calculate_period(ts_code, share_name,
                                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                     i_i, ai_i, b_i, ab_i, fi_i,
                                     report_period, forecast_period,
                                     forecast_nprofit, forecast_nprofit_ly, forecast_revenue, forecast_revenue_ly,
                                     forecast_nassets,
                                     express.ann_date)
                )
            e_i = e_i + 1
        elif same_period(adjust_balance_arr, ab_i, period_delta(from_period, -4)):
            report_period = adjust_balance_arr[ab_i].end_date
            forecast_period = report_period
            session.add(
                calculate_period(ts_code, share_name,
                                 adjust_income_arr, adjust_income_arr, adjust_balance_arr, adjust_balance_arr, fina_arr,
                                 ai_i, ai_i, ab_i, ab_i, fi_i,
                                 report_period, forecast_period,
                                 forecast_nprofit, forecast_nprofit_ly, forecast_revenue, forecast_revenue_ly,
                                 forecast_nassets,
                                 adjust_balance_arr[ab_i].f_ann_date)
            )
            ab_i = ab_i + 1
            if same_period(adjust_balance_arr, ab_i, period_delta(from_period, -4)):
                ai_i = ai_i + 1
            else:
                ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -3))
        elif same_period(balance_arr, b_i, from_period):
            report_period = balance_arr[b_i].end_date
            forecast_period = report_period
            session.add(
                calculate_period(ts_code, share_name,
                                 income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                 i_i, ai_i, b_i, ab_i, fi_i,
                                 report_period, forecast_period,
                                 forecast_nprofit, forecast_nprofit_ly, forecast_revenue, forecast_revenue_ly,
                                 forecast_nassets,
                                 balance_arr[b_i].f_ann_date)
            )
            b_i = b_i + 1
            if same_period(income_arr, i_i, from_period):
                i_i = i_i + 1
            else:
                i_i = get_index_by_end_date(income_arr, period_delta(from_period, 1))
            if same_period(fina_arr, fi_i, from_period):
                fi_i = fi_i + 1
            else:
                fi_i = get_index_by_end_date(fina_arr, period_delta(from_period, 1))
        else:
            from_period = next_period(from_period)
            b_i = get_index_by_end_date(balance_arr, from_period, b_i)
            ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -4), ab_i)
            i_i = get_index_by_end_date(income_arr, from_period, i_i)
            ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -4), ai_i)
            fi_i = get_index_by_end_date(fina_arr, from_period, fi_i)
            f_i = get_index_by_end_date(forecast_arr, from_period, f_i)
            e_i = get_index_by_end_date(express_arr, from_period, e_i)

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
