from decimal import Decimal

from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler

log = get_logger(__name__)


class SimCenter(object):
    h: SimHandler
    c: SimContext

    def __init__(self, handler: SimHandler,
                 sd: str, ed: str, cash: Decimal = 500000, charge: Decimal = 0.00025, tax: Decimal = 5):
        self.h = handler
        self.c = SimContext(sd, ed, cash, charge, tax)

    def run(self):
        while not self.c.is_finish():
            self.c.day_init()
            self.h.auction_before_trade(self.c)
            self.c.deal_after_morning_auction()
            self.c.deal_after_afternoon_auction()
            self.day_end()
