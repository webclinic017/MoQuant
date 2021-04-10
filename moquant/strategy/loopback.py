from moquant.simulator.sim_center import SimCenter
from strategy.fool_strategy import FoolStrategyHandler


def run_grow_strategy(st, ed):
    strategy: FoolStrategyHandler = FoolStrategyHandler()
    center: SimCenter = SimCenter(strategy, st, ed)
    center.run()
