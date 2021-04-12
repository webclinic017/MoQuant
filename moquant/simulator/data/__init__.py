from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_trade_cal import TsTradeCal
from moquant.log import get_logger

log = get_logger(__name__)


class SimDataService(object):

    def __init__(self):
        pass

    def get_trade_calendar(self, st, ed):
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
        log.info('Init trade cal')
        return sz, sh

    def get_daily_metrics(self,
                          ts_codes: dict(type=list, help="股票编码列表"),
                          metrics: dict(type=list, help="指标列表"),
                          dates: dict(type=list, help="日期列表")):
        pass
