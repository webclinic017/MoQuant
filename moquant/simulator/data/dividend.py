from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger

log = get_logger(__name__)


class SimDividendService(object):
    def __init__(self):
        pass

    def get_dividend_in_record_day(self, rd: str):
        """
        获取该日的分红登记股权
        :param rd: 股权登记日
        """
        session: Session = db_client.get_session()
        d_list: list = session.query(TsDividend).filter(TsDividend.record_date == rd, TsDividend.div_proc == '实施').all()
        session.close()
        return d_list
