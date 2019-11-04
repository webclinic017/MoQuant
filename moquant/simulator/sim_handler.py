from moquant.simulator.sim_context import SimContext


class SimHandler(object):

    def auction_before_trade(self, context: SimContext):
        pass

    def auction_before_end(self, context: SimContext):
        pass
