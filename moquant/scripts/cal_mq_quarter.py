import sys
import time
from decimal import Decimal
from operator import and_

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_period
from moquant.dbclient import db_client
from moquant.dbclient.mq_manual_forecast import MqManualForecast
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


class ForecastInfo(object):
    forecast_period: str
    forecast_revenue: Decimal
    forecast_nprofit: Decimal
    forecast_dprofit: Decimal
    forecast_nassets: Decimal
    forecast_nprofit_ly: Decimal
    forecast_revenue_ly: Decimal

    def __init__(self, forecast_period=None, forecast_revenue=None, forecast_nprofit=None,
                 forecast_dprofit=None, forecast_nassets=None,
                 forecast_nprofit_ly=None, forecast_revenue_ly=None):
        self.forecast_period = forecast_period
        self.forecast_revenue = forecast_revenue
        self.forecast_nprofit = forecast_nprofit
        self.forecast_dprofit = forecast_dprofit
        self.forecast_nassets = forecast_nassets
        self.forecast_nprofit_ly = forecast_nprofit_ly
        self.forecast_revenue_ly = forecast_revenue_ly
        pass

    def update_with(self, other):
        if other is None:
            return
        if other.forecast_period is not None:
            self.forecast_period = other.forecast_period
        if other.forecast_revenue is not None:
            self.forecast_revenue = other.forecast_revenue
        if other.forecast_nprofit is not None:
            self.forecast_nprofit = other.forecast_nprofit
        if other.forecast_dprofit is not None:
            self.forecast_dprofit = other.forecast_dprofit
        if other.forecast_nassets is not None:
            self.forecast_nassets = other.forecast_nassets
        if other.forecast_nprofit_ly is not None:
            self.forecast_nprofit_ly = other.forecast_nprofit_ly
        if other.forecast_revenue_ly is not None:
            self.forecast_revenue_ly = other.forecast_revenue_ly

    def init_with_forecast(self, period: str, forecast: TsForecast, income_arr, i_i, adjust_income_arr, ai_i):
        self.forecast_period = period
        income_forecast_ly = find_previous_period(adjust_income_arr, ai_i, period, 4, sub_arr=income_arr, sub_pos=i_i)
        forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_forecast_ly)
        if self.forecast_nprofit is None and forecast_min_nprofit is not None:
            self.forecast_nprofit = forecast_min_nprofit
        if self.forecast_nprofit_ly is None and forecast.last_parent_net is not None:
            self.forecast_nprofit_ly = forecast.last_parent_net * 10000

    def init_with_express(self, period: str, express: TsExpress):
        self.forecast_period = period
        if self.forecast_nprofit is None:
            self.forecast_nprofit = express.n_income
        if self.forecast_revenue is None:
            self.forecast_revenue = express.revenue
        if self.forecast_nassets is None:
            self.forecast_nassets = express.total_hldr_eqy_exc_min_int
        if self.forecast_nprofit_ly is None:
            self.forecast_nprofit_ly = express.yoy_net_profit
        if self.forecast_revenue_ly is None:
            self.forecast_revenue_ly = express.or_last_year

    def update_with_manual(self, manual: MqManualForecast):
        if manual.revenue is not None:
            self.forecast_revenue = manual.revenue
        if manual.nprofit is not None:
            self.forecast_nprofit = manual.nprofit
        if manual.dprofit is not None:
            self.forecast_dprofit = manual.dprofit


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


def find_previous_period(arr: list, pos: int, period: str, num: int, sub_arr: list = None, sub_pos: int = None):
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

    if sub_arr is not None and sub_pos is not None:
        if sub_pos >= len(sub_arr):
            sub_pos = len(sub_arr) - 1
        while sub_pos >= 0 and sub_arr[sub_pos].end_date != to_find_period \
                and sub_arr[sub_pos].ann_date >= to_find_period:
            sub_pos -= 1
        if sub_pos >= 0 and sub_arr[sub_pos].end_date == to_find_period:
            return sub_arr[sub_pos]

    return None


def same_period(arr, i: int, period: str) -> bool:
    return 0 <= i < len(arr) and arr[i].end_date == period


def same_f_ann_date(arr, i, adjust_arr, ai) -> bool:
    if i < 0 or i >= len(arr):
        return False
    if ai < 0 or ai >= len(adjust_arr):
        return False
    return arr[i].f_ann_date == adjust_arr[ai].f_ann_date


def calculate_period(ts_code, share_name,
                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                     i_i, ai_i, b_i, ab_i, fi_i,
                     report_period, forecast_period,
                     forecast_info: ForecastInfo,
                     f_ann_date, is_adjust
                     ):
    report_quarter = get_quarter_num(report_period)
    forecast_quarter = get_quarter_num(forecast_period)

    # incase there is no report for adjust
    main_income_arr = adjust_income_arr if is_adjust else income_arr
    sub_income_arr = income_arr if is_adjust else adjust_income_arr
    main_i_i = ai_i if is_adjust else i_i
    sub_i_i = i_i if is_adjust else ai_i

    main_bs_arr = adjust_balance_arr if is_adjust else balance_arr
    sub_bs_arr = balance_arr if is_adjust else adjust_balance_arr
    main_b_i = ab_i if is_adjust else b_i
    sub_b_i = b_i if is_adjust else ab_i

    income: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 0,
                                            sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l1: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 1,
                                               sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l3: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 3,
                                               sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l4: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 4,
                                               sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l5: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 5,
                                               sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_lyy: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, report_quarter,
                                                sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_forecast_lyy: TsIncome = find_previous_period(main_income_arr, main_i_i, forecast_period, forecast_quarter,
                                                         sub_arr=sub_income_arr, sub_pos=sub_i_i)

    balance: TsBalanceSheet = find_previous_period(main_bs_arr, main_b_i, report_period, 0,
                                                   sub_arr=sub_bs_arr, sub_pos=sub_b_i)

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
    if forecast_info.forecast_nprofit is None:
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
        nprofit = forecast_info.forecast_nprofit
        nprofit_ly = forecast_info.forecast_nprofit_ly
        nprofit_ly_l1 = None
        if income is not None:
            quarter_nprofit = cal_quarter_value(forecast_info.forecast_nprofit, income.n_income_attr_p, forecast_period)
        if nprofit_ly is None:
            nprofit_ly = get_first_not_none([adjust_income_l3, income_l3], 'n_income_attr_p')
        if nprofit_ly_l1 is None:
            nprofit_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')

        if nprofit_ly is not None and nprofit_ly_l1 is not None:
            quarter_nprofit_ly = cal_quarter_value(nprofit_ly, nprofit_ly_l1, forecast_period)

        if income_l3 is not None and income_l3.n_income_attr_p is not None:
            nprofit_adjust = nprofit_ly - income_l3.n_income_attr_p

        if income_forecast_lyy is not None:
            nprofit_ltm = cal_ltm(forecast_info.forecast_nprofit, nprofit_ly, income_forecast_lyy.n_income_attr_p,
                                  nprofit_adjust, forecast_period)

    dprofit_period = None
    dprofit = None
    dprofit_ly = None
    quarter_dprofit = None
    quarter_dprofit_ly = None
    dprofit_ltm = None
    # Calculate dprofit
    if forecast_info.forecast_dprofit is not None or forecast_info.forecast_nprofit is not None:
        # Forecast dprofit
        dprofit_period = forecast_period
        dprofit = forecast_info.forecast_dprofit
        if dprofit is None:
            dprofit = forecast_info.forecast_nprofit
            if fina is not None and income is not None \
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
    else:
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

    # Calculate revenue
    revenue_period = None
    revenue = None
    revenue_ly = None
    quarter_revenue = None
    quarter_revenue_ly = None
    revenue_adjust = 0
    revenue_ltm = None
    if forecast_info.forecast_revenue is None:
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

        if income_l4 is not None and income_l4.revenue is not None:
            revenue_adjust = revenue_ly - income_l4.revenue

        if revenue is not None and income_lyy is not None:
            revenue_ltm = cal_ltm(revenue, revenue_ly, income_lyy.revenue, revenue_adjust, report_period)
    else:
        # forecast
        revenue_period = forecast_period
        revenue = forecast_info.forecast_revenue
        revenue_ly = forecast_info.forecast_revenue_ly
        revenue_ly_l1 = None
        if income is not None:
            quarter_revenue = cal_quarter_value(forecast_info.forecast_revenue, income.revenue, forecast_period)

        if revenue_ly is None:
            revenue_ly = get_first_not_none([adjust_income_l3, income_l3], 'revenue')
        if revenue_ly_l1 is None:
            revenue_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'revenue')

        if revenue_ly is not None and revenue_ly_l1 is not None:
            quarter_revenue_ly = cal_quarter_value(revenue_ly, revenue_ly_l1, forecast_period)

        if income_l3 is not None and income_l3.revenue is not None:
            revenue_adjust = revenue_ly - income_l3.revenue

        if income_forecast_lyy is not None:
            revenue_ltm = cal_ltm(forecast_info.forecast_revenue, revenue_ly, income_forecast_lyy.revenue,
                                  revenue_adjust, forecast_period)

    nassets = None
    if forecast_info.forecast_nassets is None:
        if balance is not None:
            nassets = balance.total_hldr_eqy_exc_min_int
    else:
        nassets = forecast_info.forecast_nassets

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

    if revenue is None:
        revenue_period = None
    if nprofit is None:
        nprofit_period = None
    if dprofit is None:
        dprofit_period = None

    return MqQuarterBasic(ts_code=ts_code, share_name=share_name, update_date=format_delta(f_ann_date, -1),
                          report_period=report_period, forecast_period=forecast_period,
                          revenue_period=revenue_period, revenue=revenue, revenue_ly=revenue_ly,
                          revenue_yoy=revenue_yoy, quarter_revenue=quarter_revenue, revenue_ltm=revenue_ltm,
                          quarter_revenue_ly=quarter_revenue_ly, quarter_revenue_yoy=quarter_revenue_yoy,
                          nprofit_period=nprofit_period, nprofit=nprofit, nprofit_ly=nprofit_ly,
                          nprofit_yoy=nprofit_yoy, quarter_nprofit=quarter_nprofit,
                          quarter_nprofit_ly=quarter_nprofit_ly, quarter_nprofit_yoy=quarter_nprofit_yoy,
                          nprofit_ltm=nprofit_ltm, dprofit_period=dprofit_period, dprofit=dprofit,
                          dprofit_ly=dprofit_ly, dprofit_yoy=dprofit_yoy, quarter_dprofit=quarter_dprofit,
                          quarter_dprofit_ly=quarter_dprofit_ly, quarter_dprofit_yoy=quarter_dprofit_yoy,
                          dprofit_ltm=dprofit_ltm, nassets=nassets)


def calculate(ts_code, share_name, fix_from: str = None):
    result_list = []
    start_time = time.time()
    now_date = get_current_dt()
    max_period = get_period(int(now_date[0:4]), 12)
    forecast_update_date = '20010101'

    session = db_client.get_session()
    last_basic_arr = session.query(MqQuarterBasic).filter(MqQuarterBasic.ts_code == ts_code) \
        .order_by(MqQuarterBasic.update_date.desc()).limit(1).all()
    last_basic: MqQuarterBasic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_period = fix_from
    if from_period is None:
        from_period = mq_calculate_start_period
        if last_basic is not None:
            from_period = next_period(last_basic.report_period)
            if last_basic.report_period < last_basic.forecast_period:
                forecast_update_date = format_delta(last_basic.update_date, 1)

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

    forecast_manual_arr = session.query(MqManualForecast) \
        .filter(and_(MqManualForecast.ts_code == ts_code, MqManualForecast.end_date >= period_to_get)) \
        .order_by(MqManualForecast.end_date.asc(), MqManualForecast.forecast_type.asc()).all()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    b_i = get_index_by_end_date(balance_arr, from_period)
    ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -4))
    i_i = get_index_by_end_date(income_arr, from_period)
    ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -4))
    fi_i = get_index_by_end_date(fina_arr, from_period)
    f_i = get_index_by_end_date(forecast_arr, from_period)
    e_i = get_index_by_end_date(express_arr, from_period)
    fm_i = get_index_by_end_date(forecast_manual_arr, from_period)

    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_period <= max_period:
        if same_period(income_arr, i_i, from_period) and same_period(adjust_income_arr, ai_i, from_period) and \
                same_f_ann_date(income_arr, i_i, adjust_income_arr, ai_i):
            i_i += 1
            b_i = get_index_by_end_date(balance_arr, period_delta(from_period, 1))
            continue
        if same_period(balance_arr, b_i, from_period) and same_period(adjust_balance_arr, ab_i, from_period) and \
                same_f_ann_date(balance_arr, b_i, adjust_balance_arr, ab_i):
            b_i += 1
            i_i = get_index_by_end_date(income_arr, period_delta(from_period, 1))
            continue

        report_period = None
        forecast_info = ForecastInfo()

        if same_period(forecast_arr, f_i, from_period):
            forecast: TsForecast = forecast_arr[f_i]
            if forecast_update_date != forecast.ann_date:
                report_period = period_delta(from_period, -1)
                forecast_period = from_period
                forecast_info.init_with_forecast(from_period, forecast, income_arr, i_i, adjust_income_arr, ai_i)
                if same_period(forecast_manual_arr, fm_i, from_period):
                    forecast_manual: MqManualForecast = forecast_manual_arr[fm_i]
                    if forecast_manual.forecast_type == 0:
                        forecast_info.update_with_manual(forecast_manual)
                        fm_i += 1

                if same_period(express_arr, e_i, from_period):
                    express: TsExpress = express_arr[e_i]
                    if express.ann_date == forecast.ann_date:
                        express_info = ForecastInfo()
                        express_info.init_with_express(from_period, express)
                        forecast_info.update_with(express_info)
                        e_i = e_i + 1
                        if same_period(forecast_manual_arr, fm_i, from_period):
                            forecast_manual: MqManualForecast = forecast_manual_arr[fm_i]
                            if forecast_manual.forecast_type == 1:
                                forecast_info.update_with_manual(forecast_manual)
                                fm_i += 1

                result_list.append(
                    calculate_period(ts_code, share_name,
                                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                     i_i, ai_i, b_i, ab_i, fi_i,
                                     report_period, forecast_period, forecast_info,
                                     forecast.ann_date, False)
                )
            f_i = f_i + 1
        elif same_period(express_arr, e_i, from_period):
            express: TsExpress = express_arr[e_i]
            if forecast_update_date != express.ann_date:
                report_period = period_delta(from_period, -1)
                forecast_period = from_period
                forecast_info.init_with_express(from_period, express)
                result_list.append(
                    calculate_period(ts_code, share_name,
                                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                     i_i, ai_i, b_i, ab_i, fi_i,
                                     report_period, forecast_period, forecast_info,
                                     express.ann_date, False)
                )
            e_i = e_i + 1
        elif same_period(adjust_income_arr, ai_i, period_delta(from_period, -4)):
            report_period = adjust_income_arr[ai_i].end_date
            forecast_period = report_period
            result_list.append(
                calculate_period(ts_code, share_name,
                                 income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                 i_i, ai_i, b_i, ab_i, fi_i,
                                 report_period, forecast_period, forecast_info,
                                 adjust_income_arr[ai_i].f_ann_date, True)
            )
            ai_i = ai_i + 1
            if same_period(adjust_balance_arr, ab_i, period_delta(from_period, -4)):
                ab_i = ab_i + 1
            else:
                ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -3))
        elif same_period(income_arr, i_i, from_period):
            report_period = income_arr[i_i].end_date
            forecast_period = report_period
            result_list.append(
                calculate_period(ts_code, share_name,
                                 income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, fina_arr,
                                 i_i, ai_i, b_i, ab_i, fi_i,
                                 report_period, forecast_period, forecast_info,
                                 balance_arr[b_i].f_ann_date, False)
            )
            i_i = i_i + 1
            if same_period(balance_arr, b_i, from_period):
                b_i += 1
            else:
                b_i = get_index_by_end_date(balance_arr, period_delta(from_period, 1))
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
            fm_i = get_index_by_end_date(forecast_manual_arr, from_period, fm_i)

    calculate_time = time.time()
    log.info("Calculate data for %s: %s seconds" % (ts_code, calculate_time - find_index_time))
    return result_list


def calculate_and_insert(ts_code: str, share_name: str):
    result_list = calculate(ts_code, share_name)
    if len(result_list) > 0:
        session: Session = db_client.get_session()
        start = time.time()
        for item in result_list:  # type: MqQuarterBasic
            session.add(item)
        session.flush()
        log.info("Insert data for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert %s' % ts_code)


def calculate_all():
    session: Session = db_client.get_session()
    now_date = get_current_dt()
    mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == now_date).all()
    for mq in mq_list:
        calculate_and_insert(mq.ts_code, mq.share_name)
    session.flush()


def calculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    stock: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    calculate_and_insert(ts_code, stock.share_name)


def recalculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    session.query(MqQuarterBasic).filter(MqQuarterBasic.ts_code == ts_code).delete()
    calculate_by_code(ts_code)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        recalculate_by_code(sys.argv[1])
    else:
        calculate_all()
