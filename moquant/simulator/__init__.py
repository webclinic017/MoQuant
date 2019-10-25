from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.log import get_logger
from moquant.simulator.share_hold import ShareHold
from moquant.simulator.sim_handler import SimHandler
from moquant.tsclient import ts_client
from moquant.utils.datetime import format_delta

log = get_logger(__name__)

class SimCenter(object):
    __h: SimHandler
    __sd: str
    __ed: str
    __cash: Decimal
    __charge: Decimal
    __tax: Decimal

    __sz: set  # trade date
    __sh: set  # trade date

    __cd: str  # current date
    __shares: dict
    __records: dict

    def __init__(self, handler: SimHandler, sd: str, ed: str, cash: Decimal = 500000, charge: Decimal = 0.00025,
                 tax: Decimal = 5):
        self.__h = handler
        self.__sd = sd
        self.__ed = ed
        self.__cash = cash
        self.__shares = []
        self.__charge = charge
        self.__tax = tax

        sz = ts_client.fetch_trade_cal(exchange='SZSE', start_date=sd, end_date=ed, is_open=1)
        self.__sz = set([i for i in sz['cal_date'].items()])

        sh = ts_client.fetch_trade_cal(exchange='SSE', start_date=sd, end_date=ed, is_open=1)
        self.__sh = set([i for i in sh['cal_date'].items()])

        self.__cd = sd
        self.__shares = {}
        self.__records = {}

    def __next_date(self):
        self.__cd = format_delta(self.__cd, 1)

    def __record_after_trade(self):
        pass

    def __calculate_current_mv(self):
        session: Session = db_client.get_session()
        total = self.__cash
        if len(self.__shares) > 0:
            code_list = [i.ts_code for i in self.__shares]
            daily_list = session.query(TsDailyTradeInfo).filter(
                and_(TsDailyTradeInfo.ts_code.in_(code_list), TsDailyTradeInfo.trade_date == self.__cd)).all()
            daily_map = {}
            for daily in daily_list: # type: TsDailyTradeInfo
                daily_map[daily.ts_code] = daily

            for share in self.__shares: # type: ShareHold
                daily: TsDailyTradeInfo = daily_map[share.get_ts_code()]
                if daily is not None:
                    if daily.close is None:
                        log.error('Empty close of %s %s' % (share.get_ts_code(), self.__cd))
                    elif share.get_num() is None:
                        log.error('Empty num of %s %s' % (share.get_ts_code(), self.__cd))
                    else:
                        total = total + daily.close * share.get_num()
                else:
                    log.error('Cant find daily trade info of %s %s' % (share.get_ts_code(), self.__cd))
        return total

    def run(self):
        session: Session = db_client.get_session()
        while self.__cd < self.__ed:
            if self.__cd not in self.__sz and self.__cd not in self.__sh:
                self.__next_date()
                continue

            self.__h.auction_before_trade(self)
            self.__h.auction_before_end(self)

