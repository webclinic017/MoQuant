from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler

log = get_logger(__name__)


class FoolStrategyHandler(SimHandler):

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        pass

    def before_trade(self, context: SimContext, data: SimDataService):
        pass
