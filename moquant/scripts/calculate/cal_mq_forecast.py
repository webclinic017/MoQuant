import time
from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_period, mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_forecast_adjust import MqForecastAdjust
from moquant.dbclient.mq_forecast_agg import MqForecastAgg
from moquant.dbclient.mq_manual_report import MqManualReport
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.log import get_logger
from moquant.scripts import *
from moquant.utils.date_utils import *

log = get_logger(__name__)


def update_with_manual(agg: MqForecastAgg, manual: MqManualReport):
    agg.ts_code = manual.ts_code
    agg.ann_date = manual.ann_date
    agg.end_date = manual.end_date
    agg.forecast_type = manual.report_type
    agg.revenue = manual.revenue
    agg.revenue_ly = manual.revenue_ly
    agg.nprofit = manual.nprofit
    agg.nprofit_ly = manual.nprofit_ly
    agg.dprofit = manual.dprofit
    agg.dprofit_ly = manual.dprofit_ly
    agg.changed_reason = manual.changed_reason
    agg.manual_adjust_reason = manual.manual_adjust_reason
    agg.from_manual = True
    agg.one_time = manual.one_time


def get_forecast_nprofit_ly(forecast: TsForecast, income_ly: TsIncome):
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
            if income_ly is not None and income_ly.n_income_attr_p is not None:
                forecast_nprofit = percent * income_ly.n_income_attr_p
            elif forecast.last_parent_net is not None:
                forecast_nprofit = percent * forecast.last_parent_net * 10000
    return forecast_nprofit


def update_with_adjust(agg: MqForecastAgg, manual: MqForecastAdjust):
    if manual is None:
        return
    if manual.dprofit is not None:
        agg.dprofit = manual.dprofit
    if manual.one_time is not None and manual.one_time is True:
        agg.one_time = manual.one_time
    agg.manual_adjust_reason = manual.remark


def update_with_forecast(agg: MqForecastAgg, forecast: TsForecast, income_ly: TsIncome,
                         adjust: MqForecastAdjust):
    agg.ts_code = forecast.ts_code
    agg.ann_date = forecast.ann_date
    agg.end_date = forecast.end_date
    agg.forecast_type = 1
    forecast_min_nprofit = get_forecast_nprofit_ly(forecast, income_ly)
    if forecast_min_nprofit is not None:
        agg.nprofit = forecast_min_nprofit
    if forecast.last_parent_net is not None:
        agg.nprofit_ly = forecast.last_parent_net * 10000
    agg.changed_reason = forecast.change_reason
    agg.from_manual = False
    update_with_adjust(agg, adjust)


def update_with_express(agg: MqForecastAgg, express: TsExpress):
    agg.ts_code = express.ts_code
    agg.ann_date = express.ann_date
    agg.end_date = express.end_date
    agg.forecast_type = 2
    agg.nprofit = express.n_income
    agg.revenue = express.revenue
    agg.nprofit_ly = express.yoy_net_profit
    agg.revenue_ly = express.or_last_year


def is_valid(agg: MqForecastAgg) -> bool:
    if agg is None:
        return False
    if agg.ts_code is None or agg.ann_date is None or agg.end_date is None or agg.forecast_type is None:
        return False
    if agg.revenue is None and agg.nprofit is None and agg.dprofit is None:
        return False
    return True


def calculate(ts_code, share_name):
    start_time = time.time()
    now_date = get_current_dt()
    max_period = get_period(int(now_date[0:4]), 12)
    from_date = mq_calculate_start_date
    from_period = mq_calculate_start_period

    session = db_client.get_session()
    last_basic_arr = session.query(MqForecastAgg).filter(MqForecastAgg.ts_code == ts_code) \
        .order_by(MqForecastAgg.ann_date.desc()).limit(1).all()
    if len(last_basic_arr) > 0:
        last_basic: MqForecastAgg = last_basic_arr[0]
        from_date = format_delta(last_basic.ann_date, 1)
        from_period = last_basic.end_date

    forecast_arr = session.query(TsForecast) \
        .filter(TsForecast.ts_code == ts_code, TsForecast.ann_date >= from_date) \
        .order_by(TsForecast.ann_date.asc(), TsForecast.end_date.asc()).all()
    if len(forecast_arr) > 0 and forecast_arr[0].end_date > from_period:
        from_period = forecast_arr[0].end_date

    express_arr = session.query(TsExpress) \
        .filter(TsExpress.ts_code == ts_code, TsExpress.ann_date >= from_date) \
        .order_by(TsExpress.ann_date.asc(), TsExpress.end_date.asc()).all()
    if len(express_arr) and express_arr[0].end_date > from_period:
        from_period = express_arr[0].end_date

    forecast_adjust_arr = session.query(MqForecastAdjust) \
        .filter(MqForecastAdjust.ts_code == ts_code, MqForecastAdjust.end_date >= from_period) \
        .order_by(MqForecastAdjust.end_date.asc(), MqForecastAdjust.forecast_type.asc()).all()

    forecast_manual_arr = session.query(MqManualReport) \
        .filter(MqManualReport.ts_code == ts_code, MqManualReport.ann_date >= from_date,
                MqManualReport.end_date >= from_period, MqManualReport.report_type != 3) \
        .order_by(MqManualReport.ann_date.asc(), MqManualReport.end_date.asc()).all()

    income_arr = session.query(TsIncome) \
        .filter(
        TsIncome.ts_code == ts_code, TsIncome.end_date >= period_delta(from_period, -4), TsIncome.report_type == 1) \
        .order_by(TsIncome.mq_ann_date.asc(), TsIncome.end_date.asc()).all()

    session.close()

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    i_i = get_index_by_end_date(income_arr, period_delta(from_period, -4))
    f_i = get_index_by_end_date(forecast_arr, from_period)
    e_i = get_index_by_end_date(express_arr, from_period)
    fa_i = get_index_by_end_date(forecast_adjust_arr, from_period)
    fm_i = get_index_by_end_date(forecast_manual_arr, from_period)

    find_index_time = time.time()
    log.info("Find index for %s: %s seconds" % (ts_code, find_index_time - prepare_time))
    result_list = []
    while from_period <= max_period:
        agg = MqForecastAgg()
        if same_period(forecast_manual_arr, fm_i, from_period):
            update_with_manual(agg, forecast_manual_arr[fm_i])
            fa_i += 1
            from_period = next_period(from_period)
        elif same_period(forecast_arr, f_i, from_period):
            forecast: TsForecast = forecast_arr[f_i]
            if not (same_period(express_arr, e_i, from_period) and express_arr[e_i].ann_date == forecast.ann_date):
                income_ly = income_arr[i_i] if same_period(income_arr, i_i, period_delta(from_period, -4)) else None
                adjust = forecast_adjust_arr[fa_i] if same_period(forecast_adjust_arr, fa_i, from_period) else None
                update_with_forecast(agg, forecast, income_ly, adjust)
            f_i = f_i + 1
        elif same_period(express_arr, e_i, from_period):
            express: TsExpress = express_arr[e_i]
            update_with_express(agg, express)
            e_i = e_i + 1
        else:
            from_period = next_period(from_period)
        i_i = get_index_by_end_date(income_arr, period_delta(from_period, -4), i_i)
        f_i = get_index_by_end_date(forecast_arr, from_period, f_i)
        e_i = get_index_by_end_date(express_arr, from_period, e_i)
        fm_i = get_index_by_end_date(forecast_manual_arr, from_period, fm_i)
        if is_valid(agg):
            result_list.append(agg)

    calculate_time = time.time()
    log.info("Calculate data for %s: %s seconds" % (ts_code, calculate_time - find_index_time))
    return result_list


def calculate_and_insert(ts_code: str, share_name: str):
    result_list = calculate(ts_code, share_name)
    if len(result_list) > 0:
        session: Session = db_client.get_session()
        start = time.time()
        for item in result_list:  # type: MqForecastAgg
            session.add(item)
        session.flush()
        session.close()
        log.info("Insert mq_forecast_agg for %s: %s seconds" % (ts_code, time.time() - start))


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
    session.query(MqForecastAgg).filter(MqForecastAgg.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code)


if __name__ == '__main__':
    calculate_by_code('300222.SZ')
