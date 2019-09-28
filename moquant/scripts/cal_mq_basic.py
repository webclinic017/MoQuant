#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlalchemy import and_

from moquant import log
from moquant.constants import basic_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_basic_all import MqStockBasicAll
from moquant.dbclient.ts_balance_sheet import StockBalanceSheet
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


def calculate(ts_code: str):
    session = db_client.get_session()
    last_basic_arr = session.query(MqStockBasicAll).filter(MqStockBasicAll.ts_code == ts_code) \
        .order_by(MqStockBasicAll.date.desc()).limit(1).all()
    last_basic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_date = basic_start_date
    if last_basic is not None:
        from_date = format_delta(last_basic.date, 1)

    # Get all daily basic from a date
    daily_arr = session.query(TsStockDailyBasic) \
        .filter(and_(TsStockDailyBasic.ts_code == ts_code, TsStockDailyBasic.trade_date >= from_date)) \
        .order_by(TsStockDailyBasic.trade_date.asc()).all()

    if len(daily_arr) == 0:
        return

    from_date = daily_arr[0].trade_date

    # Get all reports including last two year, to calculate ttm
    from_period = first_report_period(from_date, -2)
    income_arr = session.query(StockIncome) \
        .filter(
        and_(StockIncome.ts_code == ts_code, StockIncome.f_ann_date >= from_period, StockIncome.report_type == 1)) \
        .order_by(StockIncome.f_ann_date.asc()).all()

    balance_arr = session.query(StockBalanceSheet) \
        .filter(and_(StockBalanceSheet.ts_code == ts_code, StockBalanceSheet.f_ann_date >= from_period,
                     StockBalanceSheet.report_type == 1)) \
        .order_by(StockBalanceSheet.f_ann_date.asc()).all()

    forecast_arr = session.query(StockForecast) \
        .filter(and_(StockForecast.ts_code == ts_code, StockForecast.ann_date >= from_period)) \
        .order_by(StockForecast.ann_date.asc()).all()

    express_arr = session.query(StockExpress) \
        .filter(and_(StockExpress.ts_code == ts_code, StockExpress.ann_date >= from_period)) \
        .order_by(StockExpress.ann_date.asc()).all()

    d_i = get_start_index(daily_arr, 'trade_date', from_date)
    # index of balance
    b_i = get_start_index(balance_arr, 'f_ann_date', from_date)
    # index of income
    i_i = get_start_index(income_arr, 'f_ann_date', from_date)
    f_i = get_start_index(forecast_arr, 'ann_date', from_date)
    e_i = get_start_index(express_arr, 'ann_date', from_date)

    now_date = get_current_dt()
    count = 0
    while from_date <= now_date:
        daily_basic: TsStockDailyBasic = daily_arr[d_i]
        balance: StockBalanceSheet = balance_arr[b_i] if b_i >= 0 else None
        income: StockIncome = income_arr[i_i] if i_i >= 0 else None
        forecast: StockForecast = forecast_arr[f_i] if f_i >= 0 else None
        express: StockExpress = express_arr[e_i] if e_i >= 0 else None

        report_period_arr = [getattr(report, 'end_date') if report is not None else None
                             for report in [balance, income]]
        report_season = date_max(report_period_arr)
        forecast_period_arr = [getattr(report, 'end_date') if report is not None else None
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
                season_nprofit = express.n_income - income.n_income_attr_p
                season_revenue = express.revenue - income.revenue
                if i_i - 4 >= 0:
                    season_nprofit_ly = income_arr[i_i - 3].n_income_attr_p - income_arr[i_i - 4].n_income_attr_p
                    season_revenue_ly = income_arr[i_i - 3].revenue - income_arr[i_i - 4].revenue
                if i_i - 3 >= 0:
                    nprofit_ltm = express.n_income + (
                            income_arr[i_i - quarter + 1].n_income_attr_p - income_arr[i_i - 3].n_income_attr_p)
                nassets = express.total_hldr_eqy_exc_min_int
            elif forecast is not None and forecast_season == forecast.end_date:
                forecast_nprofit = (forecast.p_change_min * forecast.last_parent_net / 100
                                    if forecast.net_profit_min is None else forecast.net_profit_min) * 10000
                season_nprofit = forecast_nprofit - income.n_income_attr_p
                if i_i - 4 >= 0:
                    season_nprofit_ly = income_arr[i_i - 3].n_income_attr_p - income_arr[i_i - 4].n_income_attr_p
                if i_i - 1 >= 0:
                    season_revenue = income_arr[i_i].revenue - income_arr[i_i - 1].revenue
                if i_i - 5 >= 0:
                    season_revenue_ly = income_arr[i_i - 4].revenue - income_arr[i_i - 5].revenue
                if i_i - 3 >= 0:
                    nprofit_ltm = forecast_nprofit + (
                            income_arr[i_i - quarter + 1].n_income_attr_p - income_arr[i_i - 3].n_income_attr_p)
                nassets = balance.total_hldr_eqy_exc_min_int
        elif report_season is not None:
            quarter = get_quarter_num(report_season)
            if i_i - 1 >= 0:
                season_nprofit = income_arr[i_i].n_income_attr_p - income_arr[i_i - 1].n_income_attr_p
                season_revenue = income_arr[i_i].revenue - income_arr[i_i - 1].revenue
            if i_i - 5 >= 0:
                season_nprofit_ly = income_arr[i_i - 4].n_income_attr_p - income_arr[i_i - 5].n_income_attr_p
                season_revenue_ly = income_arr[i_i - 4].revenue - income_arr[i_i - 5].revenue
            if i_i - 4 >= 0:
                nprofit_ltm = income_arr[i_i].n_income_attr_p + (
                        income_arr[i_i - quarter + 1].n_income_attr_p - income_arr[i_i - 4].n_income_attr_p)
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
                                    nassets=nassets, pb=pb)
        session.add(to_insert)
        count += 1
        if count == 1000:
            log.info('Insert stock basic %s %s' % (ts_code, from_date))
            session.flush()
            count = 0

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

    if count > 0:
        session.flush()


if __name__ == '__main__':
    calculate('000001.SZ')
