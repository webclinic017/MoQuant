from sqlalchemy.orm import Session

from moquant.constants import mq_daily_metric_enum
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.dbclient.mq_share_pool import MqSharePool
from moquant.log import get_logger

log = get_logger(__name__)

__strategy = 'grow_score'


def run(dt: str, min_grow_score=50):
    """
    参考 cal_grow
    筛选最后 grow_score > min_grow_score 的
    :return:
    """
    s: Session = db_client.get_session()
    s.query(MqSharePool).filter(MqSharePool.strategy == __strategy, MqSharePool.dt == dt).delete()

    daily_list: list = s.query(MqDailyMetric) \
        .filter(MqDailyMetric.update_date == dt, MqDailyMetric.name == mq_daily_metric_enum.grow_score.name,
                MqDailyMetric.value > min_grow_score) \
        .all()

    if len(daily_list) == 0:
        log.info('No grow pool in %s' % dt)
        return

    to_insert = []

    for mq in daily_list:  # type: MqDailyMetric
        to_insert.append(MqSharePool(dt=dt, strategy=__strategy, ts_code=mq.ts_code))

    db_client.batch_insert(to_insert)
    log.info('Grow strategy done. Dt: %s. Total: %d' % (dt, len(to_insert)))
