import time

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date, mq_message_type, \
    mq_quarter_metric_enum, mq_report_type
from moquant.dbclient import db_client
from moquant.dbclient.mq_message import MqMessage
from moquant.dbclient.mq_quarter_metric import MqQuarterMetric
from moquant.dbclient.ts_basic import TsBasic
from moquant.log import get_logger
from moquant.service import mq_quarter_store
from moquant.utils import date_utils, decimal_utils

log = get_logger(__name__)


def get_report_type_name(report_type):
    report_type_name = '财报'
    if (report_type & (1 << mq_report_type.report)) > 0:
        report_type_name = '财报'
    elif (report_type & (1 << mq_report_type.forecast)) > 0:
        report_type_name = '预报'
    elif (report_type & (1 << mq_report_type.express)) > 0:
        report_type_name = '快报'
    return report_type_name


def get_report_message_content(dprofit: MqQuarterMetric, share_name: str) -> str:
    pub = '%s(%s) 发布%s%s' % (
    share_name, dprofit.ts_code, date_utils.q_format_period(dprofit.period), get_report_type_name(dprofit.report_type))
    d = '扣非净利为%s' % decimal_utils.unit_format(dprofit.value)
    yoy = '同比增速为%s' % decimal_utils.percent_format(dprofit.yoy) if dprofit is not None else ''
    full = '%s,%s %s' % (pub, d, yoy)
    return full.strip()


def generate_report_message_by_code(ts_code: str, share_name: str, to_date: str = date_utils.get_current_dt()):
    result_list = []
    from_date = mq_calculate_start_date
    session = db_client.get_session()
    last_one: MqMessage = session.query(MqMessage) \
        .filter(MqMessage.ts_code == ts_code, MqMessage.msg_type <= 3) \
        .order_by(MqMessage.pub_date.desc()).limit(1).all()
    if len(last_one) > 0:
        from_date = date_utils.format_delta(last_one[0].pub_date, 1)

    quarter_store = mq_quarter_store.init_quarter_store_by_date(ts_code, from_date)
    session.close()

    while from_date <= to_date:  # type: MqQuarterBasic
        latest = quarter_store.find_latest(ts_code, mq_quarter_metric_enum.dprofit.name, from_date)
        if latest is None:
            from_date = date_utils.format_delta(from_date, 1)
            continue
        for i in range(5):
            period = date_utils.period_delta(latest.period, -i)
            dprofit = quarter_store.find_period_exact(ts_code, mq_quarter_metric_enum.dprofit.name, period,
                                                      from_date)
            if dprofit is None:
                continue
            # 只保留官方财报
            if not ((dprofit.report_type & (1 << mq_report_type.report)) > 0 or \
                    (dprofit.report_type & (1 << mq_report_type.forecast)) > 0 or \
                    (dprofit.report_type & (1 << mq_report_type.express)) > 0):
                continue
            result_list.append(MqMessage(ts_code=ts_code, msg_type=mq_message_type.report,
                                         message=get_report_message_content(dprofit, share_name),
                                         pub_date=date_utils.format_delta(from_date, 1)))
        from_date = date_utils.format_delta(from_date, 1)

    return result_list


def calculate_by_code(ts_code, to_date: str = date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    basic: TsBasic = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).one()
    session.close()
    if basic is None:
        log.error("Cant find ts_basic of %s" % ts_code)
        return
    report_message_list = generate_report_message_by_code(ts_code, basic.name, to_date)

    if len(report_message_list) > 0:
        start = time.time()
        db_client.batch_insert(report_message_list)
        log.info("Insert mq_message for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert into mq_message %s' % ts_code)


def recalculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    session.query(MqMessage).filter(MqMessage.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code, to_date)


def remove_from_date(ts_code: str, from_date: str):
    session: Session = db_client.get_session()
    session.query(MqMessage).filter(MqMessage.ts_code == ts_code,
                                    MqMessage.pub_date >= from_date).delete()
    session.close()

