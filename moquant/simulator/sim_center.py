from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.log import get_logger
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_record import SimDailyRecord
from moquant.simulator.sim_handler import SimHandler
from moquant.utils.datetime import format_delta

log = get_logger(__name__)


class SimCenter(object):
    __h: SimHandler
    __c: SimContext

    def __init__(self, handler: SimHandler, context: SimContext):
        self.__h = handler
        self.__c = context

    def __next_date(self):
        self.__cd = format_delta(self.__cd, 1)

    def __record_after_trade(self):
        self.__records[self.__cd] = SimDailyRecord(self.__cd, mv=self.__calculate_current_mv())

    def __calculate_current_mv(self):
        session: Session = db_client.get_session()
        total = self.__cash
        if len(self.__shares) > 0:
            code_list = [i.ts_code for i in self.__shares]
            daily_list = session.query(TsDailyTradeInfo).filter(
                and_(TsDailyTradeInfo.ts_code.in_(code_list), TsDailyTradeInfo.trade_date == self.__cd)).all()
            daily_map = {}
            for daily in daily_list:  # type: TsDailyTradeInfo
                daily_map[daily.ts_code] = daily

            for share in self.__shares:  # type: SimShareHold
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
        while self.__cd < self.__ed:
            if self.__cd not in self.__sz and self.__cd not in self.__sh:
                self.__next_date()
                continue

            self.__h.auction_before_trade(self.__c)
            self.__h.auction_before_end(self.__c)
