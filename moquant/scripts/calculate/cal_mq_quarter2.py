import time
from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_quarter_index import MqQuarterIndex
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.log import get_logger
from moquant.service.mq_quarter_store import MqQuarterStore
from moquant.utils.date_utils import format_delta

log = get_logger(__name__)


def init_quarter_store(ts_code, from_period=mq_calculate_start_date) -> MqQuarterStore:
    store = MqQuarterStore()
    session: Session = db_client.get_session()
    arr = session.query(MqQuarterIndex).filter(MqQuarterIndex.ts_code == ts_code, MqQuarterIndex.period >= from_period).all()
    for i in arr:
        store.add(i)
    session.close()
    return store


def calculate(ts_code: str, share_name: str, from_date: str = None):
    session: Session = db_client.get_session()
    if from_date is None:
        latest: list = session.query(MqQuarterIndex).filter(MqQuarterIndex.ts_code == ts_code) \
            .order_by(MqQuarterIndex.update_date.desc()).limit(1).all()
        if len(latest) > 0:
            from_date = format_delta(latest[0].update_date, 1)
        else:
            from_date = mq_calculate_start_date
    store = init_quarter_store(ts_code, format_delta(from_date, -1000))


def calculate_and_insert(ts_code: str, share_name: str):
    result_list = calculate(ts_code, share_name)
    if len(result_list) > 0:
        session: Session = db_client.get_session()
        start = time.time()
        for item in result_list:  # type: MqQuarterBasic
            session.add(item)
        session.flush()
        session.close()
        log.info("Insert mq_quarter_index for %s: %s seconds" % (ts_code, time.time() - start))
    else:
        log.info('Nothing to insert into mq_quarter_index %s' % ts_code)


def calculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    stock: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    session.close()
    calculate_and_insert(ts_code, stock.share_name)
