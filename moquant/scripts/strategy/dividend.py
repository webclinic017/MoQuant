from sqlalchemy.orm import Session

from moquant.constants import mq_daily_metric_enum
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.dbclient.mq_share_pool import MqSharePool
from moquant.log import get_logger

log = get_logger(__name__)

__strategy = 'dividend'


def run(dt: str, min_val_score=50):
    """
    参考 cal_val
    筛选最后 val_score > min_val_score 的
    :return:
    """
    s: Session = db_client.get_session()
    s.query(MqSharePool).filter(MqSharePool.strategy == __strategy, MqSharePool.dt == dt).delete()

    daily_list: list = s.query(MqDailyMetric) \
        .filter(MqDailyMetric.update_date == dt, MqDailyMetric.name == mq_daily_metric_enum.val_score.name,
                MqDailyMetric.value > min_val_score) \
        .all()

    if len(daily_list) == 0:
        log.info('No dividend pool in %s' % dt)
        return

    to_insert = []

    for mq in daily_list:  # type: MqDailyMetric
        to_insert.append(MqSharePool(dt=dt, strategy=__strategy, ts_code=mq.ts_code))

    db_client.batch_insert(to_insert)
    log.info('Dividend strategy done. Dt: %s. Total: %d' % (dt, len(to_insert)))
