import time

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_message import MqMessage
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.log import get_logger
from moquant.utils.date_utils import format_delta, q_format_period
from moquant.utils.decimal_utils import unit_format, percent_format

log = get_logger(__name__)


def get_report_type_name(forecast_type, report_period, forecast_period):
    report_type_name = '财报'
    period = report_period
    if forecast_type is None:
        report_type_name = '财报'
    elif forecast_type == 1:
        report_type_name = '预报'
        period = forecast_period
    elif forecast_type == 2:
        report_type_name = '快报'
        period = forecast_period
    return '%s%s' % (q_format_period(period), report_type_name)


def generate_report_message_by_code(ts_code: str):
    result_list = []
    from_date = mq_calculate_start_date
    session = db_client.get_session()
    last_one: MqMessage = session.query(MqMessage) \
        .filter(MqMessage.ts_code == ts_code, MqMessage.msg_type == 1) \
        .order_by(MqMessage.pub_date.desc()).limit(1).all()
    if len(last_one) > 0:
        from_date = format_delta(last_one[0].pub_date, 1)

    quarter_list = session.query(MqQuarterBasic) \
        .filter(MqQuarterBasic.ts_code == ts_code, MqQuarterBasic.update_date >= from_date,
                MqQuarterBasic.adjust_ly == '0') \
        .order_by(MqQuarterBasic.update_date.asc(), MqQuarterBasic.forecast_period.asc(),
                  MqQuarterBasic.report_period.asc()) \
        .all()
    session.close()

    for quarter in quarter_list:  # type: MqQuarterBasic
        message = '%s(%s) 发布%s，扣非净利为%s，同比增速为%s' % \
                  (quarter.share_name, quarter.ts_code,
                   get_report_type_name(quarter.forecast_type, quarter.report_period, quarter.forecast_period),
                   unit_format(quarter.dprofit), percent_format(quarter.dprofit_yoy))
        result_list.append(MqMessage(ts_code=ts_code, msg_type=1, message=message, pub_date=quarter.update_date))

    return result_list


def calculate_by_code(ts_code):
    report_message_list = generate_report_message_by_code(ts_code)

    start = time.time()
    session: Session = db_client.get_session()
    for item in report_message_list:  # type: MqMessage
        session.add(item)
    session.flush()
    session.close()
    log.info("Insert data for %s: %s seconds" % (ts_code, time.time() - start))


def recalculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    session.query(MqMessage).filter(MqMessage.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code)

if __name__ == '__main__':
    recalculate_by_code('300552.SZ')