from decimal import Decimal

from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler
from simulator.data import SimDataService

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
        self.h: SimHandler = handler
        self.d: SimDataService = SimDataService(sd, ed)
        self.c: SimContext = SimContext(self.d, sd, ed, cash, charge, tax, pass_tax)

    def run(self):
        while not self.c.is_finish():
            self.c.day_init()
            self.h.morning_auction(self.c, self.d)
            self.c.deal_after_morning_auction()
            self.h.before_trade(self.c, self.d)
            self.c.deal_after_afternoon_auction()
            self.c.day_end()
        self.c.analyse()
