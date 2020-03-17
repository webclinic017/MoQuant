import sys
import time
from functools import partial

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_period
from moquant.dbclient import db_client
from moquant.dbclient.mq_forecast_agg import MqForecastAgg
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.scripts import *
from moquant.utils.date_utils import *
from moquant.utils.decimal_utils import *

log = get_logger(__name__)


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


def add_ltm(mrq, l1, l2, l3, field):
    result = Decimal(0)
    if mrq is not None and getattr(mrq, field) is not None:
        result += getattr(mrq, field)
    if l1 is not None and getattr(l1, field) is not None:
        result += getattr(l1, field)
    if l2 is not None and getattr(l2, field) is not None:
        result += getattr(l2, field)
    if l3 is not None and getattr(l3, field) is not None:
        result += getattr(l3, field)
    return result


def get_first_not_none(arr, field_name):
    for item in arr:
        if item is not None and getattr(item, field_name) is not None:
            return getattr(item, field_name)
    return None


def find_previous_period(arr: list, pos: int, period: str, num: int, date_field: str = 'ann_date',
                         sub_arr: list = None, sub_pos: int = None):
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
    while pos >= 0 and arr[pos].end_date != to_find_period and getattr(arr[pos], date_field) >= to_find_period:
        pos -= 1
    if pos >= 0 and arr[pos].end_date == to_find_period:
        return arr[pos]

    if sub_arr is not None and sub_pos is not None:
        if sub_pos >= len(sub_arr):
            sub_pos = len(sub_arr) - 1
        while sub_pos >= 0 and sub_arr[sub_pos].end_date != to_find_period \
                and getattr(sub_arr[sub_pos], date_field) >= to_find_period:
            sub_pos -= 1
        if sub_pos >= 0 and sub_arr[sub_pos].end_date == to_find_period:
            return sub_arr[sub_pos]

    return None


def same_field(arr, i, adjust_arr, ai, field: str) -> bool:
    if i < 0 or i >= len(arr):
        return False
    if ai < 0 or ai >= len(adjust_arr):
        return False
    return getattr(arr[i], field) == getattr(adjust_arr[ai], field)


def cal_quarter_dividend(balance: TsBalanceSheet, dividend: TsDividend):
    if balance is None or dividend is None:
        return 0
    if balance.total_share is None or dividend.cash_div_tax is None:
        return 0
    return balance.total_share * dividend.cash_div_tax


def cal_dividend(report_period, main_balance_arr, sub_balance_arr, mb_i, sb_i,
                 dividend_arr, d_i):
    balance: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 0,
                                                   date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l1: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 1,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l2: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 2,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l3: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 3,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l4: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 4,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l5: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 5,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l6: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 6,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)
    balance_l7: TsBalanceSheet = find_previous_period(main_balance_arr, mb_i, report_period, 7,
                                                      date_field='mq_ann_date', sub_arr=sub_balance_arr, sub_pos=sb_i)

    dividend: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 0)
    dividend_l1: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 1)
    dividend_l2: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 2)
    dividend_l3: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 3)
    dividend_l4: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 4)
    dividend_l5: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 5)
    dividend_l6: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 6)
    dividend_l7: TsDividend = find_previous_period(dividend_arr, d_i, report_period, 7)

    quarter_dividend = cal_quarter_dividend(balance, dividend)
    dividend_ltm = add(cal_quarter_dividend(balance, dividend), cal_quarter_dividend(balance_l1, dividend_l1),
                       cal_quarter_dividend(balance_l2, dividend_l2), cal_quarter_dividend(balance_l3, dividend_l3))
    dividend_ltm_ly = add(cal_quarter_dividend(balance_l4, dividend_l4), cal_quarter_dividend(balance_l5, dividend_l5),
                          cal_quarter_dividend(balance_l6, dividend_l6), cal_quarter_dividend(balance_l7, dividend_l7))

    return quarter_dividend, dividend_ltm, yoy(dividend_ltm, dividend_ltm_ly)


def cal_other_info(quarter: MqQuarterBasic, income: TsIncome, balance: TsBalanceSheet, cf: TsCashFlow):
    total_nprofit = None
    run_cf = None

    if income is not None:
        total_nprofit = income.n_income

    if balance is not None:
        quarter.eps = div(quarter.dprofit_ltm, balance.total_share)

        total_receive = add(balance.notes_receiv, balance.accounts_receiv, balance.oth_receiv, balance.lt_rec)
        revenue = quarter.revenue_ltm
        quarter.receive_risk = div(total_receive, revenue)

        quarter.liquidity_risk = div(balance.total_cur_liab, balance.total_cur_assets)

        total_intangible = add(balance.goodwill, balance.r_and_d, balance.intan_assets)
        total_assests = sub(quarter.nassets, balance.oth_eqt_tools_p_shr)
        quarter.intangible_risk = div(total_intangible, total_assests)
        quarter.cash_debt_rate = div(add(balance.money_cap, balance.oth_cur_assets),
                                     add(balance.lt_borr, balance.st_borr))
    else:
        log.warn('Cant find balance sheet of %s %s' % (quarter.ts_code, quarter.report_period))

    if cf is not None:
        run_cf = cf.n_cashflow_act
    else:
        log.warn('Cant find cash flow sheet of %s %s' % (quarter.ts_code, quarter.report_period))

    quarter.nprofit_to_cf = div(total_nprofit, run_cf)
    quarter.dividend_profit_ratio = div(quarter.dividend_ltm, quarter.dprofit_ltm)

    return quarter


def cal_nprofit(report_period, forecast_period, forecast_info: MqForecastAgg,
                income, income_l1, income_l3, income_l4, income_l5, income_lyy,
                adjust_income_l3, adjust_income_l4, adjust_income_l5, income_forecast_lyy):
    nprofit_period = None
    nprofit = None
    nprofit_ly = None
    quarter_nprofit = None
    quarter_nprofit_ly = None
    nprofit_adjust = 0
    nprofit_ltm = None
    # Calculate nprofit
    if forecast_info.nprofit is None:
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
        nprofit = forecast_info.nprofit
        nprofit_ly = forecast_info.nprofit_ly
        nprofit_ly_l1 = None
        if income is not None:
            quarter_nprofit = cal_quarter_value(forecast_info.nprofit, income.n_income_attr_p, forecast_period)
        if nprofit_ly is None:
            nprofit_ly = get_first_not_none([adjust_income_l3, income_l3], 'n_income_attr_p')
        if nprofit_ly_l1 is None:
            nprofit_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')

        if nprofit_ly is not None and nprofit_ly_l1 is not None:
            quarter_nprofit_ly = cal_quarter_value(nprofit_ly, nprofit_ly_l1, forecast_period)

        if income_l3 is not None and income_l3.n_income_attr_p is not None:
            nprofit_adjust = nprofit_ly - income_l3.n_income_attr_p

        if income_forecast_lyy is not None:
            nprofit_ltm = cal_ltm(forecast_info.nprofit, nprofit_ly, income_forecast_lyy.n_income_attr_p,
                                  nprofit_adjust, forecast_period)

    nprofit_yoy = yoy(nprofit, nprofit_ly)
    quarter_nprofit_yoy = yoy(quarter_nprofit, quarter_nprofit_ly)

    if nprofit is None:
        nprofit_period = None

    return nprofit_period, nprofit, nprofit_ly, quarter_nprofit, quarter_nprofit_ly, nprofit_adjust, nprofit_ltm, \
           nprofit_yoy, quarter_nprofit_yoy


def cal_dprofit(report_period, forecast_period, forecast_info: MqForecastAgg,
                fina, fina_l1, fina_l3, fina_l4, fina_l5, fina_lyy,
                income, nprofit_adjust):
    dprofit_period = None
    dprofit = None
    dprofit_ly = None
    quarter_dprofit = None
    quarter_dprofit_ly = None
    dprofit_ltm = None
    # Calculate dprofit
    if forecast_info.dprofit is not None or forecast_info.nprofit is not None:
        # Forecast dprofit
        dprofit_period = forecast_period
        dprofit = forecast_info.dprofit
        if dprofit is None:
            dprofit = forecast_info.nprofit
            if fina is not None and income is not None \
                    and income.n_income_attr_p is not None and fina.profit_dedt is not None\
                    and get_quarter_num(fina.end_date) != 4 and get_quarter_num(income.end_date) != 4:
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

    dprofit_yoy = yoy(dprofit, dprofit_ly)
    quarter_dprofit_yoy = yoy(quarter_dprofit, quarter_dprofit_ly)

    if dprofit is None:
        dprofit_period = None

    return dprofit_period, dprofit, dprofit_ly, quarter_dprofit, quarter_dprofit_ly, dprofit_ltm, \
           dprofit_yoy, quarter_dprofit_yoy, forecast_info.one_time


def cal_revenue(report_period, forecast_period, forecast_info: MqForecastAgg,
                income, income_l1, income_l3, income_l4, income_l5, income_lyy,
                adjust_income_l3, adjust_income_l4, adjust_income_l5, income_forecast_lyy):
    # Calculate revenue
    revenue_period = None
    revenue = None
    revenue_ly = None
    quarter_revenue = None
    quarter_revenue_ly = None
    revenue_adjust = 0
    revenue_ltm = None
    if forecast_info.revenue is None:
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
        revenue = forecast_info.revenue
        revenue_ly = forecast_info.revenue_ly
        revenue_ly_l1 = None
        if income is not None:
            quarter_revenue = cal_quarter_value(forecast_info.revenue, income.revenue, forecast_period)

        if revenue_ly is None:
            revenue_ly = get_first_not_none([adjust_income_l3, income_l3], 'revenue')
        if revenue_ly_l1 is None:
            revenue_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'revenue')

        if revenue_ly is not None and revenue_ly_l1 is not None:
            quarter_revenue_ly = cal_quarter_value(revenue_ly, revenue_ly_l1, forecast_period)

        if income_l3 is not None and income_l3.revenue is not None:
            revenue_adjust = revenue_ly - income_l3.revenue

        if income_forecast_lyy is not None:
            revenue_ltm = cal_ltm(forecast_info.revenue, revenue_ly, income_forecast_lyy.revenue,
                                  revenue_adjust, forecast_period)

    revenue_yoy = yoy(revenue, revenue_ly)
    quarter_revenue_yoy = yoy(quarter_revenue, quarter_revenue_ly)

    if revenue is None:
        revenue_period = None

    return revenue_period, revenue, revenue_ly, quarter_revenue, quarter_revenue_ly, revenue_adjust, revenue_ltm, \
           revenue_yoy, quarter_revenue_yoy


def cal_du_pont(quarter: MqQuarterBasic, balance_arr: list):
    for i in range(4):
        if balance_arr[i] is None:
            balance_arr[i] = TsBalanceSheet()
    avg_nasset = avg_in_exists(balance_arr[0].total_hldr_eqy_exc_min_int, balance_arr[1].total_hldr_eqy_exc_min_int,
                               balance_arr[2].total_hldr_eqy_exc_min_int, balance_arr[3].total_hldr_eqy_exc_min_int)
    avg_total_assets = avg_in_exists(balance_arr[0].total_assets, balance_arr[1].total_assets,
                                     balance_arr[2].total_assets, balance_arr[3].total_assets)
    quarter.roe = div(quarter.dprofit_ltm, avg_nasset)
    quarter.dprofit_margin = div(quarter.dprofit_ltm, quarter.revenue_ltm)
    quarter.turnover_rate = div(quarter.revenue_ltm, avg_total_assets)
    quarter.equity_multiplier = div(avg_total_assets, avg_nasset)


def calculate_period(ts_code, share_name,
                     income_arr, adjust_income_arr, balance_arr, adjust_balance_arr, cash_arr, adjust_cash_arr,
                     fina_arr, dividend_arr,
                     i_i, ai_i, b_i, ab_i, c_i, ac_i,
                     fi_i, d_i,
                     report_period, forecast_period,
                     forecast_info: MqForecastAgg,
                     ann_date, is_adjust
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

    main_cf_arr = adjust_cash_arr if is_adjust else cash_arr
    sub_cf_arr = cash_arr if is_adjust else adjust_cash_arr
    main_c_i = ac_i if is_adjust else c_i
    sub_c_i = c_i if is_adjust else ac_i

    income: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 0,
                                            date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l1: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 1,
                                               date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l3: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 3,
                                               date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l4: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 4,
                                               date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_l5: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, 5,
                                               date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_lyy: TsIncome = find_previous_period(main_income_arr, main_i_i, report_period, report_quarter,
                                                date_field='mq_ann_date', sub_arr=sub_income_arr, sub_pos=sub_i_i)
    income_forecast_lyy: TsIncome = find_previous_period(main_income_arr, main_i_i, forecast_period, forecast_quarter,
                                                         date_field='mq_ann_date', sub_arr=sub_income_arr,
                                                         sub_pos=sub_i_i)

    balance: TsBalanceSheet = find_previous_period(main_bs_arr, main_b_i, report_period, 0,
                                                   date_field='mq_ann_date', sub_arr=sub_bs_arr, sub_pos=sub_b_i)
    balance_l1: TsBalanceSheet = find_previous_period(main_bs_arr, main_b_i, report_period, 1,
                                                      date_field='mq_ann_date', sub_arr=sub_bs_arr, sub_pos=sub_b_i)
    balance_l2: TsBalanceSheet = find_previous_period(main_bs_arr, main_b_i, report_period, 2,
                                                      date_field='mq_ann_date', sub_arr=sub_bs_arr, sub_pos=sub_b_i)
    balance_l3: TsBalanceSheet = find_previous_period(main_bs_arr, main_b_i, report_period, 3,
                                                      date_field='mq_ann_date', sub_arr=sub_bs_arr, sub_pos=sub_b_i)

    cash: TsCashFlow = find_previous_period(main_cf_arr, main_c_i, report_period, 0,
                                            date_field='mq_ann_date', sub_arr=sub_cf_arr, sub_pos=sub_c_i)

    adjust_income_l3: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 3,
                                                      date_field='mq_ann_date')
    adjust_income_l4: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 4,
                                                      date_field='mq_ann_date')
    adjust_income_l5: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_period, 5,
                                                      date_field='mq_ann_date')

    fina: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 0)
    fina_l1: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 1)
    fina_l3: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 3)
    fina_l4: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 4)
    fina_l5: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, 5)
    fina_lyy: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_period, report_quarter)

    dividend, dividend_ltm, dividend_ltm_yoy = cal_dividend(report_period, main_bs_arr, sub_bs_arr, main_b_i, sub_b_i,
                                                            dividend_arr, d_i)

    nprofit_period, nprofit, nprofit_ly, quarter_nprofit, quarter_nprofit_ly, nprofit_adjust, nprofit_ltm, \
    nprofit_yoy, quarter_nprofit_yoy = \
        cal_nprofit(report_period, forecast_period, forecast_info,
                    income, income_l1, income_l3, income_l4, income_l5, income_lyy,
                    adjust_income_l3, adjust_income_l4, adjust_income_l5, income_forecast_lyy)

    dprofit_period, dprofit, dprofit_ly, quarter_dprofit, quarter_dprofit_ly, dprofit_ltm, \
    dprofit_yoy, quarter_dprofit_yoy, one_time = \
        cal_dprofit(report_period, forecast_period, forecast_info,
                    fina, fina_l1, fina_l3, fina_l4, fina_l5, fina_lyy,
                    income, nprofit_adjust)

    revenue_period, revenue, revenue_ly, quarter_revenue, quarter_revenue_ly, revenue_adjust, revenue_ltm, \
    revenue_yoy, quarter_revenue_yoy = \
        cal_revenue(report_period, forecast_period, forecast_info,
                    income, income_l1, income_l3, income_l4, income_l5, income_lyy,
                    adjust_income_l3, adjust_income_l4, adjust_income_l5, income_forecast_lyy)

    nassets = balance.total_hldr_eqy_exc_min_int if balance is not None else None

    ret = MqQuarterBasic(ts_code=ts_code, share_name=share_name, update_date=format_delta(ann_date, -1),
                         report_period=report_period, adjust_ly=is_adjust,
                         forecast_period=forecast_period, forecast_type=forecast_info.forecast_type,
                         revenue_period=revenue_period, revenue=revenue, revenue_ly=revenue_ly,
                         revenue_yoy=revenue_yoy, quarter_revenue=quarter_revenue, revenue_ltm=revenue_ltm,
                         quarter_revenue_ly=quarter_revenue_ly, quarter_revenue_yoy=quarter_revenue_yoy,
                         nprofit_period=nprofit_period, nprofit=nprofit, nprofit_ly=nprofit_ly,
                         nprofit_yoy=nprofit_yoy, quarter_nprofit=quarter_nprofit,
                         quarter_nprofit_ly=quarter_nprofit_ly, quarter_nprofit_yoy=quarter_nprofit_yoy,
                         nprofit_ltm=nprofit_ltm, dprofit_period=dprofit_period, dprofit=dprofit,
                         dprofit_ly=dprofit_ly, dprofit_yoy=dprofit_yoy, quarter_dprofit=quarter_dprofit,
                         quarter_dprofit_ly=quarter_dprofit_ly, quarter_dprofit_yoy=quarter_dprofit_yoy,
                         dprofit_ltm=dprofit_ltm, dprofit_forecast_one_time=one_time, nassets=nassets,
                         dividend=dividend, dividend_ltm=dividend_ltm, dividend_ltm_yoy=dividend_ltm_yoy)
    cal_other_info(ret, income, balance, cash)
    cal_du_pont(ret, [balance, balance_l1, balance_l2, balance_l3])
    return ret


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
        .order_by(TsIncome.mq_ann_date.asc(), TsIncome.end_date.asc()).all()

    adjust_income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.end_date >= period_to_get, TsIncome.report_type == 4) \
        .order_by(TsIncome.mq_ann_date.asc(), TsIncome.end_date.asc()).all()

    balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= period_to_get,
                TsBalanceSheet.report_type == 1) \
        .order_by(TsBalanceSheet.mq_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    adjust_balance_arr = session.query(TsBalanceSheet) \
        .filter(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= period_to_get,
                TsBalanceSheet.report_type == 4) \
        .order_by(TsBalanceSheet.mq_ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

    cash_arr = session.query(TsCashFlow) \
        .filter(TsCashFlow.ts_code == ts_code, TsCashFlow.end_date >= period_to_get,
                TsCashFlow.report_type == 1) \
        .order_by(TsCashFlow.mq_ann_date.asc(), TsCashFlow.end_date.asc()).all()

    adjust_cash_arr = session.query(TsCashFlow) \
        .filter(TsCashFlow.ts_code == ts_code, TsCashFlow.end_date >= period_to_get,
                TsCashFlow.report_type == 4) \
        .order_by(TsCashFlow.mq_ann_date.asc(), TsCashFlow.end_date.asc()).all()

    fina_arr = session.query(TsFinaIndicator) \
        .filter(TsFinaIndicator.ts_code == ts_code, TsFinaIndicator.end_date >= period_to_get,
                TsFinaIndicator.ann_date != None) \
        .order_by(TsFinaIndicator.ann_date.asc(), TsFinaIndicator.end_date.asc()).all()

    dividend_arr = session.query(TsDividend) \
        .filter(TsDividend.ts_code == ts_code, TsDividend.end_date >= period_to_get,
                TsDividend.div_proc == '实施') \
        .order_by(TsDividend.end_date.asc()).all()

    forecast_arr = session.query(MqForecastAgg) \
        .filter(MqForecastAgg.ts_code == ts_code, MqForecastAgg.end_date >= period_to_get) \
        .order_by(MqForecastAgg.end_date.asc(), MqForecastAgg.ann_date.asc()).all()

    session.close()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    b_i = get_index_by_end_date(balance_arr, from_period)
    ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -4))
    i_i = get_index_by_end_date(income_arr, from_period)
    ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -4))
    c_i = get_index_by_end_date(cash_arr, from_period)
    ac_i = get_index_by_end_date(adjust_cash_arr, period_delta(from_period, -4))
    fi_i = get_index_by_end_date(fina_arr, from_period)
    f_i = get_index_by_end_date(forecast_arr, from_period)
    d_i = get_index_by_end_date(dividend_arr, from_period)

    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_period <= max_period:
        call_cal = partial(calculate_period, ts_code=ts_code, share_name=share_name,
                           income_arr=income_arr, adjust_income_arr=adjust_income_arr,
                           balance_arr=balance_arr, adjust_balance_arr=adjust_balance_arr,
                           cash_arr=cash_arr, adjust_cash_arr=adjust_cash_arr,
                           fina_arr=fina_arr, dividend_arr=dividend_arr,
                           i_i=i_i, ai_i=ai_i, b_i=b_i, ab_i=ab_i, c_i=c_i, ac_i=ac_i,
                           fi_i=fi_i, d_i=d_i)

        if same_period(forecast_arr, f_i, from_period):
            forecast: MqForecastAgg = forecast_arr[f_i]
            if forecast_update_date < forecast.ann_date:
                report_period = period_delta(from_period, -1)
                forecast_period = from_period
                result_list.append(
                    call_cal(report_period=report_period, forecast_period=forecast_period,
                             ann_date=forecast.ann_date, is_adjust=False, forecast_info=forecast)
                )
            f_i = f_i + 1
        elif same_period(income_arr, i_i, from_period):
            report_period = income_arr[i_i].end_date
            forecast_period = report_period
            result_list.append(
                call_cal(report_period=report_period, forecast_period=forecast_period,
                         ann_date=income_arr[i_i].mq_ann_date, is_adjust=False, forecast_info=MqForecastAgg())
            )
            if same_period(dividend_arr, d_i, from_period) and \
                dividend_arr[d_i].imp_ann_date == income_arr[i_i].mq_ann_date:
                    d_i += 1

            i_i = i_i + 1
            if same_period(balance_arr, b_i, from_period):
                b_i += 1
            else:
                b_i = get_index_by_end_date(balance_arr, period_delta(from_period, 1))
            if same_period(fina_arr, fi_i, from_period):
                fi_i = fi_i + 1
            else:
                fi_i = get_index_by_end_date(fina_arr, period_delta(from_period, 1))
        elif same_period(adjust_income_arr, ai_i, from_period):
            report_period = adjust_income_arr[ai_i].end_date
            forecast_period = report_period
            result_list.append(
                call_cal(report_period=report_period, forecast_period=forecast_period,
                         ann_date=adjust_income_arr[ai_i].mq_ann_date, is_adjust=True, forecast_info=MqForecastAgg())
            )
            if same_period(dividend_arr, d_i, from_period) and \
                    dividend_arr[d_i].imp_ann_date == adjust_income_arr[ai_i].mq_ann_date:
                d_i += 1

            ai_i = ai_i + 1
            if same_period(adjust_balance_arr, ab_i, period_delta(from_period, -4)):
                ab_i = ab_i + 1
            else:
                ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -3))
        elif same_period(dividend_arr, d_i, from_period):
            report_period = dividend_arr[d_i].end_date
            forecast_period = report_period
            result_list.append(
                call_cal(report_period=report_period, forecast_period=forecast_period,
                         ann_date=dividend_arr[d_i].imp_ann_date, is_adjust=False, forecast_info=MqForecastAgg())
            )
            d_i += 1
        else:
            from_period = next_period(from_period)
            b_i = get_index_by_end_date(balance_arr, from_period, b_i)
            ab_i = get_index_by_end_date(adjust_balance_arr, period_delta(from_period, -4), ab_i)
            i_i = get_index_by_end_date(income_arr, from_period, i_i)
            ai_i = get_index_by_end_date(adjust_income_arr, period_delta(from_period, -4), ai_i)
            c_i = get_index_by_end_date(cash_arr, from_period, c_i)
            ac_i = get_index_by_end_date(adjust_cash_arr, period_delta(from_period, -4), ac_i)
            fi_i = get_index_by_end_date(fina_arr, from_period, fi_i)
            f_i = get_index_by_end_date(forecast_arr, from_period, f_i)
            d_i = get_index_by_end_date(dividend_arr, from_period, d_i)

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
        session.close()
        log.info("Insert data for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert %s' % ts_code)


def calculate_all():
    session: Session = db_client.get_session()
    now_date = get_current_dt()
    mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == now_date).all()
    session.close()
    for mq in mq_list:
        calculate_and_insert(mq.ts_code, mq.share_name)


def calculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    stock: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    session.close()
    calculate_and_insert(ts_code, stock.share_name)


def recalculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    session.query(MqQuarterBasic).filter(MqQuarterBasic.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        recalculate_by_code(sys.argv[1])
    else:
        calculate_all()