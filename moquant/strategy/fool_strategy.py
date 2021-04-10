from log import get_logger
from simulator.data import SimDataService
from simulator.sim_context import SimContext
from simulator.sim_handler import SimHandler

log = get_logger(__name__)


class FoolStrategyHandler(SimHandler):

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        pass

    def before_trade(self, context: SimContext, data: SimDataService):
        pass
