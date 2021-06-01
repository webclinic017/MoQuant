from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.utils import date_utils

log = get_logger(__name__)


class SimDividendService(object):

    def __init__(self):
        self.__cache = {}

    def init_cache(self, ts_code_set: set, from_date: str, to_date: str):
        """
        预先缓存指定日期的数据
        :param ts_code_set: 编码列表
        :param from_date: 开始日期
        :param to_date: 结束日期
        :return:
        """
        if from_date is None or not date_utils.is_valid_dt(from_date):
                raise Exception('from_date is empty or invalid')
        if to_date is None or not date_utils.is_valid_dt(to_date):
            raise Exception('to_date is empty or invalid')
        session: Session = db_client.get_session()
        d_list: list = session.query(TsDividend)\
            .filter(TsDividend.record_date.between(from_date, to_date), TsDividend.div_proc == '实施').all()
        session.close()
        for d in d_list:  # type: TsDividend
            date = d.record_date
            if date not in self.__cache:
                self.__cache[date] = []
            self.__cache[date].append(d)
        log.info("Cache init: dividend")

    def get_dividend_in_record_day(self, rd: str):
        """
        获取该日的分红登记股权
        :param rd: 股权登记日
        """
        d_list: list = []
        if rd in self.__cache:
            d_list = self.__cache[rd]
        else:
            session: Session = db_client.get_session()
            d_list: list = session.query(TsDividend).filter(TsDividend.record_date == rd, TsDividend.div_proc == '实施').all()
            session.close()
        return d_list
