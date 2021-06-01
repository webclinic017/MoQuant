import pandas as pd
import pyfolio as pf

from decimal import Decimal

from matplotlib import pyplot

from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_record import SimDailyRecord
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.data import SimDataService
from moquant.utils import date_utils

log = get_logger(__name__)


class SimCenter(object):

    def __init__(self,
                 handler: SimHandler,
                 sd: dict(type=str, help="回测开始日期"),
                 ed: dict(type=str, help="回测结束日期"),
                 cash: dict(type=Decimal, help="起始现金") = 500000,
                 charge: dict(type=Decimal, help="交易费率") = 0.00025,
                 tax: dict(type=Decimal, help="印花税率") = 0.001,
                 pass_tax: dict(type=Decimal, help="过户费率") = 0.00002):
        self.__cash = cash
        self.__sd = sd
        self.__ed = ed
        self.h: SimHandler = handler
        self.d: SimDataService = SimDataService()
        self.c: SimContext = SimContext(self.d, sd, ed, cash, charge, tax, pass_tax)
        self.__dr: dict = {}
        self.h.init(self.c, self.d)

    def run(self):
        while not self.c.is_finish():
            dt = self.c.get_dt()
            self.c.day_init()
            self.h.morning_auction(self.c, self.d)
            self.c.deal_after_morning_auction()
            self.h.before_trade(self.c, self.d)
            self.c.deal_after_afternoon_auction()
            self.c.day_end()
            self.daily_record(dt)
            self.h.after_trade(self.c, self.d)
            self.c.next_day()
        self.analyse()

    def daily_record(self, dt: str):
        """
        交易日结束后
        做净值记录
        :param dt:
        :return:
        """
        record = SimDailyRecord()
        for (ts_code, share) in self.c.get_holding().items():  # type: str, SimShareHold
            record.add_share(share)
        for (ts_code, share) in self.c.get_holding_just_buy().items():  # type: str, SimShareHold
            record.add_share(share)
        record.add_cash(self.c.get_cash())
        self.__dr[dt] = record
        log.info("[%s] Market value. cash: %.2f. share: %.2f" % (dt, record.get_cash(), record.get_share_value()))

    def analyse(self):
        d = self.__sd
        max_mv = self.__cash
        last_mv = self.__cash
        max_retrieve = 0
        ra = []
        da = []
        while d <= self.__ed:
            if d in self.__dr:
                record: SimDailyRecord = self.__dr[d]
                mv = record.get_total()
                ret = (mv - last_mv) / last_mv
                if mv > max_mv:
                    max_mv = mv
                last_mv = mv
                retrieve = (max_mv - last_mv) / max_mv
                if retrieve > max_retrieve:
                    max_retrieve = retrieve

                ra.append(float(ret))
                da.append(date_utils.parse_str(d))
            d = date_utils.format_delta(d, 1)
        returns = pd.Series(ra, da)
        pf.plot_returns(returns)
        pyplot.show()

