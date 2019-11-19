from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler

log = get_logger(__name__)


class SimCenter(object):
    h: SimHandler
    c: SimContext

    def __init__(self, handler: SimHandler, context: SimContext):
        self.h = handler
        self.c = context

    def run(self):
        self.c.day_init()
        self.h.auction_before_trade(self.c)
