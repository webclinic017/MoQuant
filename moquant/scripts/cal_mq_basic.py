#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from sqlalchemy import and_

from moquant import log
from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_basic_all import MqStockBasicAll
from moquant.dbclient.ts_balance_sheet import StockBalanceSheet
from moquant.dbclient.ts_basic import StockBasic
from moquant.dbclient.ts_daily_basic import TsStockDailyBasic
from moquant.dbclient.ts_express import StockExpress
from moquant.dbclient.ts_forecast import StockForecast
from moquant.dbclient.ts_income import StockIncome
from moquant.utils.datetime import format_delta, first_report_period, get_current_dt, date_max, get_quarter_num


def get_start_index(arr, date_field: str, current_date: str) -> int:
    i = -1
    while i + 1 < len(arr):
        if getattr(arr[i + 1], date_field) > current_date:
            break
        else:
            i += 1
    return i


def can_use_next_date(arr: list, date_field: str, i: int, current_date: str) -> bool:
    if i + 1 < len(arr) and getattr(arr[i + 1], date_field) <= current_date:
        return True
    else:
        return False


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
    year = int(period[0:4])
    month = int(period[4:6])
    for i in range(num):
        month -= 3
        if month == 0:
            year -= 1
            month = 12
    day = 30 if month == 6 or month == 9 else 31
    to_find_period = '%d%02d%02d' % (year, month, day)
    while pos >= 0 and arr[pos].end_date > to_find_period:
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

    d_i = get_start_index(daily_arr, 'trade_date', from_date)
    # index of balance
    b_i = get_start_index(balance_arr, 'f_ann_date', from_date)
    # index of income
    i_i = get_start_index(income_arr, 'f_ann_date', from_date)
    f_i = get_start_index(forecast_arr, 'ann_date', from_date)
    e_i = get_start_index(express_arr, 'ann_date', from_date)

    time_start = time.time()
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
        if forecast_season is not None and forecast_season > report_season:
            quarter = get_quarter_num(forecast_season)
            if express is not None and forecast_season == express.end_date:
                season_nprofit = cal_season_value(express.n_income, income.n_income_attr_p, express.end_date)
                season_revenue = cal_season_value(express.revenue, income.revenue, express.end_date)

                income_l4 = find_previous_period(income_arr, i_i, forecast_season, 4)
                income_l5 = find_previous_period(income_arr, i_i, forecast_season, 5)
                income_lyy = find_previous_period(income_arr, i_i, forecast_season, quarter)
                if income_l4 is not None and income_l5 is not None:
                    season_nprofit_ly = cal_season_value(income_l4.n_income_attr_p, income_l5.n_income_attr_p,
                                                         income_l4.end_date)
                    season_revenue_ly = cal_season_value(income_l4.revenue, income_l5.revenue, income_l4.end_date)
                if income_l4 is not None and income_lyy is not None:
                    nprofit_ltm = express.n_income + (income_lyy.n_income_attr_p - income_l4.n_income_attr_p)
                nassets = express.total_hldr_eqy_exc_min_int
            elif forecast is not None and forecast_season == forecast.end_date:
                income_l2 = find_previous_period(income_arr, i_i, forecast_season, 2)
                income_l4 = find_previous_period(income_arr, i_i, forecast_season, 4)
                income_l5 = find_previous_period(income_arr, i_i, forecast_season, 5)
                income_l6 = find_previous_period(income_arr, i_i, forecast_season, 6)
                income_lyy = find_previous_period(income_arr, i_i, forecast_season, quarter)

                forecast_nprofit = get_forecast_nprofit_ly(forecast, income_l4)
                season_nprofit = None
                if forecast_nprofit is not None:
                    season_nprofit = cal_season_value(forecast_nprofit, income.n_income_attr_p, forecast.end_date)

                if income_l4 is not None and income_l5 is not None:
                    season_nprofit_ly = cal_season_value(income_l4.n_income_attr_p, income_l5.n_income_attr_p,
                                                         income_l4.end_date)
                if income_l2 is not None:
                    season_revenue = cal_season_value(income.revenue, income_l2.revenue, income.end_date)
                if income_l5 is not None and income_l6 is not None:
                    season_revenue_ly = cal_season_value(income_l5.revenue, income_l6.revenue, income_l5.end_date)
                if income_l4 is not None and income_lyy is not None:
                    nprofit_ltm = forecast_nprofit + (income_lyy.n_income_attr_p - income_l4.n_income_attr_p)
                nassets = balance.total_hldr_eqy_exc_min_int
        elif report_season is not None:
            quarter = get_quarter_num(report_season)
            income_l1 = find_previous_period(income_arr, i_i, report_season, 1)
            income_l4 = find_previous_period(income_arr, i_i, report_season, 4)
            income_l5 = find_previous_period(income_arr, i_i, report_season, 5)
            income_lyy = find_previous_period(income_arr, i_i, report_season, quarter)

            if income_l1 is not None:
                season_nprofit = cal_season_value(income.n_income_attr_p, income_l1.n_income_attr_p, income.end_date)
                season_revenue = cal_season_value(income.revenue, income_l1.revenue, income.end_date)
            if income_l4 is not None and income_l5 is not None:
                season_nprofit_ly = cal_season_value(income_l4.n_income_attr_p, income_l5.n_income_attr_p,
                                                     income_l4.end_date)
                season_revenue_ly = cal_season_value(income_l4.revenue, income_l5.revenue, income_l4.end_date)
            if income_l4 is not None and income_lyy is not None:
                nprofit_ltm = income.n_income_attr_p + (income_lyy.n_income_attr_p - income_l4.n_income_attr_p)
            nassets = balance.total_hldr_eqy_exc_min_int

        nprofit_ltm_pe = None
        eps_ltm = None
        if nprofit_ltm is not None:
            nprofit_ltm_pe = market_value / nprofit_ltm
            eps_ltm = nprofit_ltm / total_share

        season_revenue_yoy = None
        revenue_peg = None
        if season_revenue is not None and season_revenue_ly is not None:
            season_revenue_yoy = (season_revenue - season_revenue_ly) / abs(season_revenue_ly)
            if nprofit_ltm_pe is not None:
                revenue_peg = nprofit_ltm_pe / season_revenue_yoy / 100

        season_nprofit_yoy = None
        nprofit_peg = None
        if season_nprofit is not None and season_nprofit_ly is not None:
            season_nprofit_yoy = (season_nprofit - season_nprofit_ly) / abs(season_nprofit_ly)
            if nprofit_ltm_pe is not None:
                nprofit_peg = nprofit_ltm_pe / season_nprofit_yoy / 100

        pb = None
        if nassets is not None:
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
        if can_use_next_date(daily_arr, 'trade_date', d_i, from_date):
            d_i += 1
        if can_use_next_date(balance_arr, 'f_ann_date', b_i, from_date):
            b_i += 1
        if can_use_next_date(income_arr, 'f_ann_date', i_i, from_date):
            i_i += 1
        if can_use_next_date(forecast_arr, 'ann_date', f_i, from_date):
            f_i += 1
        if can_use_next_date(express_arr, 'ann_date', e_i, from_date):
            e_i += 1

    print('while cost', time.time() - time_start)
    session.flush()


if __name__ == '__main__':
    calculate('002188.SZ')
