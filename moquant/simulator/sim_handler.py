from moquant.simulator.sim_context import SimContext
from moquant.simulator.data import SimDataService


class SimHandler(object):

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        pass

    def before_trade(self, context: SimContext, data: SimDataService):
        pass
