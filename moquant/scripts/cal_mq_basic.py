#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算逻辑备忘
1. 对于调整：年中财报有对去年进行调整的，计算ltm时在去年Q4上加上调整值
"""

import sys
import time

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.mq_sys_param import MqSysParam
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.utils.datetime import format_delta, first_report_period, get_current_dt, date_max, get_quarter_num

log = get_logger(__name__)


def get_start_index(arr, date_field: str, current_date: str) -> int:
    i = -1
    while i + 1 < len(arr):
        if getattr(arr[i + 1], date_field) > current_date:
            break
        else:
            i += 1
    return i


def get_next_index(arr, date_field: str, pos: str) -> int:
    if pos == len(arr):
        return None
    result = pos + 1
    while result < len(arr) and getattr(arr[result], date_field) < getattr(arr[pos], date_field):
        result += 1
    if result >= len(arr):
        return None
    else:
        return result


def can_use_next_date(arr: list, date_field: str, next_pos: int, current_date: str) -> bool:
    if next_pos is None:
        return False
    else:
        return getattr(arr[next_pos], date_field) <= current_date


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
    while pos >= 0 and arr[pos].end_date != to_find_period and arr[pos].ann_date >= to_find_period:
        pos -= 1
    if pos >= 0 and arr[pos].end_date == to_find_period:
        return arr[pos]
    else:
        return None


def cal_season_value(current, last, period: str):
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

    if adjust >= 0:
        return ans1 if ans1 is not None and ans1 >= ans2 else ans2
    else:
        return ans1 if ans1 is not None and ans1 < ans2 else ans2


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


def calculate(ts_code: str, share_name: str):
    start_time = time.time()
    now_date = get_current_dt()
    session = db_client.get_session()
    last_basic_arr = session.query(MqDailyBasic).filter(MqDailyBasic.ts_code == ts_code) \
        .order_by(MqDailyBasic.date.desc()).limit(1).all()
    last_basic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_date = mq_calculate_start_date
    if last_basic is not None:
        from_date = format_delta(last_basic.date, 1)
    else:
        ts_basic_arr = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
        if len(ts_basic_arr) > 0 and ts_basic_arr[0].list_date > from_date:
            from_date = ts_basic_arr[0].list_date
    if from_date > now_date:
        return

    # Get all daily basic from a date
    last_daily_basic = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date < from_date)) \
        .order_by(TsDailyBasic.trade_date.desc()) \
        .limit(1) \
        .all()
    daily_start_date = last_daily_basic[0].trade_date if len(last_daily_basic) > 0 else from_date
    daily_arr = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date >= daily_start_date)) \
        .order_by(TsDailyBasic.trade_date.asc()).all()
    if len(daily_arr) > 0 and daily_arr[0].trade_date > from_date:
        from_date = daily_arr[0].trade_date

    # Get all reports including last two year, to calculate ttm
    from_period = first_report_period(from_date, -2)

    income_arr = session.query(TsIncome) \
        .filter(
        and_(TsIncome.ts_code == ts_code, TsIncome.end_date >= from_period, TsIncome.report_type == 1)) \
        .order_by(TsIncome.ann_date.asc(), TsIncome.end_date.asc()).all()
    if len(income_arr) > 0 and income_arr[0].ann_date > from_date:
        from_date = income_arr[0].ann_date

    adjust_income_arr = session.query(TsIncome) \
        .filter(
        and_(TsIncome.ts_code == ts_code, TsIncome.end_date >= from_period, TsIncome.report_type == 4)) \
        .order_by(TsIncome.ann_date.asc(), TsIncome.end_date.asc()).all()

    balance_arr = session.query(TsBalanceSheet) \
        .filter(and_(TsBalanceSheet.ts_code == ts_code, TsBalanceSheet.end_date >= from_period,
                     TsBalanceSheet.report_type == 1)) \
        .order_by(TsBalanceSheet.ann_date.asc(), TsBalanceSheet.end_date.asc()).all()

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

    d_i = get_start_index(daily_arr, 'trade_date', from_date)
    # index of balance
    b_i = get_start_index(balance_arr, 'ann_date', from_date)
    # index of income
    i_i = get_start_index(income_arr, 'ann_date', from_date)
    ai_i = get_start_index(adjust_income_arr, 'ann_date', from_date)
    fi_i = get_start_index(fina_arr, 'ann_date', from_date)
    f_i = get_start_index(forecast_arr, 'ann_date', from_date)
    e_i = get_start_index(express_arr, 'ann_date', from_date)

    d_i_n = get_next_index(daily_arr, 'trade_date', d_i)
    b_i_n = get_next_index(balance_arr, 'ann_date', b_i)
    i_i_n = get_next_index(income_arr, 'ann_date', i_i)
    ai_i_n = get_next_index(adjust_income_arr, 'ann_date', ai_i)
    fi_i_n = get_next_index(fina_arr, 'ann_date', fi_i)
    f_i_n = get_next_index(forecast_arr, 'ann_date', f_i)
    e_i_n = get_next_index(express_arr, 'ann_date', e_i)
    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_date <= now_date:
        daily_basic: TsDailyBasic = daily_arr[d_i]
        is_trade_day: bool = (daily_basic.trade_date == from_date)
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
        report_season = date_max(report_period_arr)
        forecast_period_arr = [report.end_date if report is not None else None
                               for report in [income, forecast, express]]
        forecast_season = date_max(forecast_period_arr)
        total_share = daily_basic.total_share * 10000
        close = daily_basic.close
        market_value = daily_basic.total_mv * 10000

        season_nprofit = None
        season_nprofit_ly = None
        nprofit_ltm = None
        season_dprofit = None
        season_dprofit_ly = None
        dprofit_ltm = None
        season_revenue = None
        season_revenue_ly = None
        nassets = None

        forecast_quarter = get_quarter_num(forecast_season)
        report_quarter = get_quarter_num(report_season)
        forecast_nprofit = None
        forecast_nprofit_ly = None
        forecast_revenue = None
        forecast_revenue_ly = None
        forecast_nassets = None

        if forecast_season is not None and forecast_season > report_season:
            if express is not None and forecast_season == express.end_date:
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

            if forecast is not None and forecast_season == forecast.end_date:
                income_forecast_ly = find_previous_period(income_arr, i_i, forecast_season, 4)
                forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_forecast_ly)
                if forecast_nprofit is None and forecast_min_nprofit is not None:
                    forecast_nprofit = forecast_min_nprofit
                if forecast_nprofit_ly is None and forecast.last_parent_net is not None:
                    forecast_nprofit_ly = forecast.last_parent_net * 10000

        income_l1: TsIncome = find_previous_period(income_arr, i_i, report_season, 1)
        income_l3: TsIncome = find_previous_period(income_arr, i_i, report_season, 3)
        income_l4: TsIncome = find_previous_period(income_arr, i_i, report_season, 4)
        income_l5: TsIncome = find_previous_period(income_arr, i_i, report_season, 5)
        income_lyy: TsIncome = find_previous_period(income_arr, i_i, report_season, report_quarter)
        income_forecast_lyy: TsIncome = find_previous_period(income_arr, i_i, forecast_season, forecast_quarter)

        adjust_income_l3: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_season, 3)
        adjust_income_l4: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_season, 4)
        adjust_income_l5: TsIncome = find_previous_period(adjust_income_arr, ai_i, report_season, 5)

        fina_l1: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_season, 1)
        fina_l4: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_season, 4)
        fina_l5: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_season, 5)
        fina_lyy: TsFinaIndicator = find_previous_period(fina_arr, fi_i, report_season, report_quarter)

        nprofit_adjust = 0
        # Calculate nprofit
        if forecast_nprofit is None:
            # No forecast
            if income is not None and income_l1 is not None:
                season_nprofit = cal_season_value(income.n_income_attr_p, income_l1.n_income_attr_p, report_season)

            nprofit_ly = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')
            nprofit_ly_l1 = get_first_not_none([adjust_income_l5, income_l5], 'n_income_attr_p')

            if nprofit_ly is not None and nprofit_ly_l1 is not None:
                season_nprofit_ly = cal_season_value(nprofit_ly, nprofit_ly_l1, report_season)

            if income_l4 is not None and income_l4.n_income_attr_p is not None:
                nprofit_adjust = nprofit_ly - income_l4.n_income_attr_p

            if income is not None and income_lyy is not None:
                nprofit_ltm = cal_ltm(income.n_income_attr_p, nprofit_ly, income_lyy.n_income_attr_p, nprofit_adjust,
                                      report_season)
        else:
            # forecast
            nprofit_ly = forecast_nprofit_ly
            nprofit_ly_l1 = None
            if income is not None:
                season_nprofit = cal_season_value(forecast_nprofit, income.n_income_attr_p, forecast_season)
            if nprofit_ly is None:
                nprofit_ly = get_first_not_none([adjust_income_l3, income_l3], 'n_income_attr_p')
            if nprofit_ly_l1 is None:
                nprofit_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'n_income_attr_p')

            if nprofit_ly is not None and nprofit_ly_l1 is not None:
                season_nprofit_ly = cal_season_value(nprofit_ly, nprofit_ly_l1, forecast_season)

            if income_l3 is not None and income_l3.n_income_attr_p is not None:
                nprofit_adjust = nprofit_ly - income_l3.n_income_attr_p

            if income_forecast_lyy is not None:
                nprofit_ltm = cal_ltm(forecast_nprofit, nprofit_ly, income_forecast_lyy.n_income_attr_p, nprofit_adjust,
                                      forecast_season)

        # Calculate dprofit
        if True:
            dprofit_ly = None
            dprofit_ly_l1 = None
            # No forecast
            if fina is not None and fina_l1 is not None:
                season_dprofit = cal_season_value(fina.profit_dedt, fina_l1.profit_dedt, report_season)
                if fina is not None and fina_l1 is not None:
                    dprofit_ly = cal_last_year(fina.profit_dedt, fina.dt_netprofit_yoy, nprofit_adjust)
                    dprofit_ly_l1 = cal_last_year(fina_l1.profit_dedt, fina_l1.dt_netprofit_yoy, nprofit_adjust)
            if dprofit_ly is None and fina_l4 is not None:
                dprofit_ly = fina_l4.profit_dedt

            if dprofit_ly_l1 is None and fina_l5 is not None:
                dprofit_ly_l1 = fina_l5.profit_dedt

            if dprofit_ly is not None and dprofit_ly_l1 is not None:
                season_dprofit_ly = cal_season_value(dprofit_ly, dprofit_ly_l1, report_season)

            adjust = 0
            if dprofit_ly is not None and fina_l4 is not None and fina_l4.profit_dedt is not None:
                adjust = dprofit_ly - fina_l4.profit_dedt

            if fina is not None and fina_lyy is not None:
                dprofit_ltm = cal_ltm(fina.profit_dedt, dprofit_ly, fina_lyy.profit_dedt, adjust,
                                      report_season)

        # Calculate revenue
        if forecast_revenue is None:
            # No forecast
            if income is not None and income_l1 is not None:
                season_revenue = cal_season_value(income.revenue, income_l1.revenue, income.end_date)

            revenue_ly = get_first_not_none([adjust_income_l4, income_l4], 'revenue')
            revenue_ly_l1 = get_first_not_none([adjust_income_l5, income_l5], 'revenue')

            if revenue_ly and revenue_ly_l1 is not None:
                season_revenue_ly = cal_season_value(revenue_ly, revenue_ly_l1, report_season)
        else:
            # forecast
            revenue_ly = forecast_revenue_ly
            revenue_ly_l1 = None
            if income is not None:
                season_revenue = cal_season_value(forecast_revenue, income.revenue, forecast_season)

            if revenue_ly is None:
                revenue_ly = get_first_not_none([adjust_income_l3, income_l3], 'revenue')
            if revenue_ly_l1 is None:
                revenue_ly_l1 = get_first_not_none([adjust_income_l4, income_l4], 'revenue')

            if revenue_ly and revenue_ly_l1 is not None:
                season_revenue_ly = cal_season_value(revenue_ly, revenue_ly_l1, forecast_season)

        if forecast_nassets is None:
            if balance is not None:
                nassets = balance.total_hldr_eqy_exc_min_int
        else:
            nassets = forecast_nassets

        nprofit_pe = None
        nprofit_eps = None
        if nprofit_ltm is not None and nprofit_ltm != 0:
            nprofit_pe = market_value / nprofit_ltm
            nprofit_eps = nprofit_ltm / total_share

        dprofit_pe = None
        dprofit_eps = None
        if dprofit_ltm is not None and dprofit_ltm != 0:
            dprofit_pe = market_value / dprofit_ltm
            dprofit_eps = dprofit_ltm / total_share

        season_revenue_yoy = None
        if season_revenue is not None and season_revenue_ly is not None and season_revenue_ly != 0:
            season_revenue_yoy = (season_revenue - season_revenue_ly) / abs(season_revenue_ly)

        season_nprofit_yoy = None
        nprofit_peg = None
        if season_nprofit is not None and season_nprofit_ly is not None and season_nprofit_ly != 0:
            season_nprofit_yoy = (season_nprofit - season_nprofit_ly) / abs(season_nprofit_ly)
            if nprofit_pe is not None and season_nprofit_yoy != 0:
                nprofit_peg = nprofit_pe / season_nprofit_yoy / 100

        season_dprofit_yoy = None
        dprofit_peg = None
        if season_dprofit is not None and season_dprofit_ly is not None and season_dprofit_ly != 0:
            season_dprofit_yoy = (season_dprofit - season_dprofit_ly) / abs(season_dprofit_ly)
            if dprofit_pe is not None and season_dprofit_yoy != 0:
                dprofit_peg = dprofit_pe / season_dprofit_yoy / 100

        pb = None
        if nassets is not None and nassets != 0:
            pb = market_value / nassets

        to_insert = MqDailyBasic(ts_code=ts_code, share_name=share_name, date=from_date, report_season=report_season,
                                 forecast_season=forecast_season, total_share=total_share, close=close,
                                 market_value=market_value, season_revenue=season_revenue,
                                 season_revenue_ly=season_revenue_ly, season_revenue_yoy=season_revenue_yoy,
                                 season_nprofit=season_nprofit, season_nprofit_ly=season_nprofit_ly,
                                 season_nprofit_yoy=season_nprofit_yoy, nprofit_ltm=nprofit_ltm,
                                 nprofit_eps=nprofit_eps, nprofit_pe=nprofit_pe, nprofit_peg=nprofit_peg,
                                 season_dprofit=season_dprofit, season_dprofit_ly=season_dprofit_ly,
                                 season_dprofit_yoy=season_dprofit_yoy, dprofit_ltm=dprofit_ltm,
                                 dprofit_eps=dprofit_eps, dprofit_pe=dprofit_pe, dprofit_peg=dprofit_peg,
                                 nassets=nassets, pb=pb, is_trade_day=is_trade_day)
        session.add(to_insert)

        from_date = format_delta(from_date, day_num=1)
        if can_use_next_date(daily_arr, 'trade_date', d_i_n, from_date):
            d_i = d_i_n
            d_i_n = get_next_index(daily_arr, 'trade_date', d_i)

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
    param = session.query(MqSysParam).filter(MqSysParam.param_key == 'CAL_DAILY_DONE').all()
    if len(param) > 0:
        param[0].value = now_date
    else:
        session.add(MqSysParam(param_key='CAL_DAILY_DONE', param_value=now_date))
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
