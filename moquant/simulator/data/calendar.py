from sqlalchemy import and_
from sqlalchemy.orm import Session
from moquant.dbclient import db_client
from moquant.dbclient.ts_trade_cal import TsTradeCal
from moquant.log import get_logger

log = get_logger(__name__)


class SimCalendarService(object):

    def __init__(self):
        pass

    def get_trade_calendar(self, st: str, ed: str):
        """
        获取两市交易日历
        :param st: 开始日期
        :param ed: 结束日期
        :return:
        """
        sz = set()
        sh = set()
        session: Session = db_client.get_session()
        trade_list: list = session.query(TsTradeCal).filter(
            and_(TsTradeCal.cal_date >= st, TsTradeCal.cal_date <= ed, TsTradeCal.is_open == 1)).all()
        for trade in trade_list:  # type: TsTradeCal
            if trade.exchange == 'SZSE':
                sz.add(trade.cal_date)
            elif trade.exchange == 'SSE':
                sh.add(trade.cal_date)
        session.close()
        return sz, sh
