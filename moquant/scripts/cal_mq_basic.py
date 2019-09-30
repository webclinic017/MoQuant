#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_basic_all import MqStockBasicAll
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_balance_sheet import StockBalanceSheet
from moquant.dbclient.ts_basic import StockBasic
from moquant.dbclient.ts_daily_basic import TsStockDailyBasic
from moquant.dbclient.ts_express import StockExpress
from moquant.dbclient.ts_forecast import StockForecast
from moquant.dbclient.ts_income import StockIncome
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


def get_forecast_nprofit_ly(forecast: StockForecast, income_l4: StockIncome):
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
    while pos >= 0 and arr[pos].end_date != to_find_period and arr[pos].f_ann_date >= to_find_period:
        pos -= 1
    if pos >= 0 and arr[pos].end_date == to_find_period:
        return arr[pos]
    else:
        return None


def cal_season_value(current, last, period: str):
    if int(period[4:6]) == 3:
        return current
    elif current is not None and last is not None:
        return current - last
    else:
        return None


def calculate(ts_code: str):
    start_time = time.time()
    now_date = get_current_dt()
    session = db_client.get_session()
    last_basic_arr = session.query(MqStockBasicAll).filter(MqStockBasicAll.ts_code == ts_code) \
        .order_by(MqStockBasicAll.date.desc()).limit(1).all()
    last_basic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_date = mq_calculate_start_date
    if last_basic is not None:
        from_date = format_delta(last_basic.date, 1)
    else:
        ts_basic_arr = session.query(StockBasic).filter(StockBasic.ts_code == ts_code).all()
        if len(ts_basic_arr) > 0 and ts_basic_arr[0].list_date > from_date:
            from_date = ts_basic_arr[0].list_date
    if from_date > now_date:
        return

    # Get all daily basic from a date
    last_daily_basic = session.query(TsStockDailyBasic) \
        .filter(and_(TsStockDailyBasic.ts_code == ts_code, TsStockDailyBasic.trade_date < from_date)) \
        .order_by(TsStockDailyBasic.trade_date.desc()) \
        .limit(1) \
        .all()
    daily_start_date = last_daily_basic[0].trade_date if len(last_daily_basic) > 0 else from_date
    daily_arr = session.query(TsStockDailyBasic) \
        .filter(and_(TsStockDailyBasic.ts_code == ts_code, TsStockDailyBasic.trade_date >= daily_start_date)) \
        .order_by(TsStockDailyBasic.trade_date.asc()).all()
    if len(daily_arr) > 0 and daily_arr[0].trade_date > from_date:
        from_date = daily_arr[0].trade_date

    # Get all reports including last two year, to calculate ttm
    from_period = first_report_period(from_date, -2)

    income_arr = session.query(StockIncome) \
        .filter(
        and_(StockIncome.ts_code == ts_code, StockIncome.end_date >= from_period, StockIncome.report_type == 1)) \
        .order_by(StockIncome.f_ann_date.asc()).all()
    if len(income_arr) > 0 and income_arr[0].f_ann_date > from_date:
        from_date = income_arr[0].f_ann_date

    balance_arr = session.query(StockBalanceSheet) \
        .filter(and_(StockBalanceSheet.ts_code == ts_code, StockBalanceSheet.end_date >= from_period,
                     StockBalanceSheet.report_type == 1)) \
        .order_by(StockBalanceSheet.f_ann_date.asc()).all()

    forecast_arr = session.query(StockForecast) \
        .filter(and_(StockForecast.ts_code == ts_code, StockForecast.end_date >= from_period)) \
        .order_by(StockForecast.ann_date.asc()).all()

    express_arr = session.query(StockExpress) \
        .filter(and_(StockExpress.ts_code == ts_code, StockExpress.end_date >= from_period)) \
        .order_by(StockExpress.ann_date.asc()).all()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    d_i = get_start_index(daily_arr, 'trade_date', from_date)
    # index of balance
    b_i = get_start_index(balance_arr, 'f_ann_date', from_date)
    # index of income
    i_i = get_start_index(income_arr, 'f_ann_date', from_date)
    f_i = get_start_index(forecast_arr, 'ann_date', from_date)
    e_i = get_start_index(express_arr, 'ann_date', from_date)

    d_i_n = get_next_index(daily_arr, 'trade_date', d_i)
    b_i_n = get_next_index(balance_arr, 'f_ann_date', b_i)
    i_i_n = get_next_index(income_arr, 'f_ann_date', i_i)
    f_i_n = get_next_index(forecast_arr, 'ann_date', f_i)
    e_i_n = get_next_index(express_arr, 'ann_date', e_i)
    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))

    while from_date <= now_date:
        daily_basic: TsStockDailyBasic = daily_arr[d_i]
        is_trade_day: bool = (daily_basic.trade_date == from_date)
        balance: StockBalanceSheet = balance_arr[b_i] if b_i >= 0 else None
        income: StockIncome = income_arr[i_i] if i_i >= 0 else None
        forecast: StockForecast = forecast_arr[f_i] if f_i >= 0 else None
        # filter useless forecast
        if forecast is not None and \
                (forecast.p_change_min is None and forecast.p_change_max is None and
                 forecast.net_profit_min is None and forecast.net_profit_max is None):
            forecast = None
        express: StockExpress = express_arr[e_i] if e_i >= 0 else None

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
        season_revenue = None
        season_revenue_ly = None
        nassets = None

        forecast_quarter = get_quarter_num(forecast_season)
        report_quarter = get_quarter_num(report_season)
        forecast_nprofit = None
        forecast_revenue = None
        forecast_nassets = None

        if forecast_season is not None and forecast_season > report_season:
            if express is not None and forecast_season == express.end_date:
                if express.n_income is not None:
                    forecast_nprofit = express.n_income
                if express.revenue is not None:
                    forecast_revenue = express.revenue
                if express.total_hldr_eqy_exc_min_int is not None:
                    forecast_nassets = express.total_hldr_eqy_exc_min_int
            if forecast is not None and forecast_season == forecast.end_date:
                income_forecast_ly = find_previous_period(income_arr, i_i, forecast_season, 4)
                forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_forecast_ly)
                if forecast_nprofit is None and forecast_min_nprofit is not None:
                    forecast_nprofit = forecast_min_nprofit

        income_l1 = find_previous_period(income_arr, i_i, report_season, 1)
        # income_l2 = find_previous_period(income_arr, i_i, report_season, 2)
        income_l3 = find_previous_period(income_arr, i_i, report_season, 3)
        income_l4 = find_previous_period(income_arr, i_i, report_season, 4)
        income_l5 = find_previous_period(income_arr, i_i, report_season, 5)
        # income_l6 = find_previous_period(income_arr, i_i, report_season, 6)
        income_lyy = find_previous_period(income_arr, i_i, report_season, report_quarter)
        income_forecast_lyy = find_previous_period(income_arr, i_i, forecast_season, forecast_quarter)

        # Calculate nprofit
        if forecast_nprofit is None:
            # No forecast
            if income is not None and income_l1 is not None:
                season_nprofit = cal_season_value(income.n_income_attr_p, income_l1.n_income_attr_p, income.end_date)
            if income_l4 is not None and income_l5 is not None:
                season_nprofit_ly = cal_season_value(income_l4.n_income_attr_p, income_l5.n_income_attr_p,
                                                     income_l4.end_date)
            if income_l4 is not None and income_lyy is not None:
                nprofit_ltm = income.n_income_attr_p + (income_lyy.n_income_attr_p - income_l4.n_income_attr_p)
        else:
            # forecast
            if income is not None:
                season_nprofit = cal_season_value(forecast_nprofit, income.n_income_attr_p, forecast_season)
            if income_l3 is not None and income_l4 is not None:
                season_nprofit_ly = cal_season_value(income_l3.n_income_attr_p, income_l4.n_income_attr_p,
                                                     income_l3.end_date)
            if income_l3 is not None and income_forecast_lyy is not None:
                nprofit_ltm = forecast_nprofit + (income_forecast_lyy.n_income_attr_p - income_l3.n_income_attr_p)

        # Calculate revenue
        if forecast_revenue is None:
            # No forecast
            if income_l1 is not None:
                season_revenue = cal_season_value(income.revenue, income_l1.revenue, income.end_date)
            if income_l4 is not None and income_l5 is not None:
                season_revenue_ly = cal_season_value(income_l4.revenue, income_l5.revenue, income_l4.end_date)
        else:
            # forecast
            if income is not None:
                season_revenue = cal_season_value(forecast_revenue, income.revenue, forecast_season)
            if income_l3 is not None and income_l4 is not None:
                season_revenue_ly = cal_season_value(income_l3.revenue, income_l4.revenue, income_l3.end_date)

        if forecast_nassets is None:
            nassets = balance.total_hldr_eqy_exc_min_int
        else:
            nassets = forecast_nassets

        nprofit_ltm_pe = None
        eps_ltm = None
        if nprofit_ltm is not None and nprofit_ltm != 0:
            nprofit_ltm_pe = market_value / nprofit_ltm
            eps_ltm = nprofit_ltm / total_share

        season_revenue_yoy = None
        revenue_peg = None
        if season_revenue is not None and season_revenue_ly is not None and season_revenue_ly != 0:
            season_revenue_yoy = (season_revenue - season_revenue_ly) / abs(season_revenue_ly)
            if nprofit_ltm_pe is not None and season_revenue_yoy != 0:
                revenue_peg = nprofit_ltm_pe / season_revenue_yoy / 100

        season_nprofit_yoy = None
        nprofit_peg = None
        if season_nprofit is not None and season_nprofit_ly is not None and season_nprofit_ly != 0:
            season_nprofit_yoy = (season_nprofit - season_nprofit_ly) / abs(season_nprofit_ly)
            if nprofit_ltm_pe is not None and season_nprofit_yoy != 0:
                nprofit_peg = nprofit_ltm_pe / season_nprofit_yoy / 100

        pb = None
        if nassets is not None and nassets != 0:
            pb = market_value / nassets

        to_insert = MqStockBasicAll(ts_code=ts_code, date=from_date, report_season=report_season,
                                    forecast_season=forecast_season, total_share=total_share, close=close,
                                    market_value=market_value, nprofit_ltm=nprofit_ltm, nprofit_ltm_pe=nprofit_ltm_pe,
                                    eps_ltm=eps_ltm, season_revenue=season_revenue, season_revenue_ly=season_revenue_ly,
                                    season_revenue_yoy=season_revenue_yoy, revenue_peg=revenue_peg,
                                    season_nprofit=season_nprofit, season_nprofit_ly=season_nprofit_ly,
                                    season_nprofit_yoy=season_nprofit_yoy, nprofit_peg=nprofit_peg,
                                    nassets=nassets, pb=pb, is_trade_day=is_trade_day)
        session.add(to_insert)

        from_date = format_delta(from_date, day_num=1)
        if can_use_next_date(daily_arr, 'trade_date', d_i_n, from_date):
            d_i = d_i_n
            d_i_n = get_next_index(daily_arr, 'trade_date', d_i)

        if can_use_next_date(balance_arr, 'f_ann_date', b_i_n, from_date):
            b_i = b_i_n
            b_i_n = get_next_index(balance_arr, 'f_ann_date', b_i)
        if can_use_next_date(income_arr, 'f_ann_date', i_i_n, from_date):
            i_i = i_i_n
            i_i_n = get_next_index(income_arr, 'f_ann_date', i_i)
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
    mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.last_handle_date == now_date).all()
    for mq in mq_list:
        calculate(mq.ts_code)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        calculate(sys.argv[1])
    else:
        calculate_all()
