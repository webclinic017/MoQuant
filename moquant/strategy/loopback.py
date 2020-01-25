from moquant.simulator.sim_center import SimCenter
from moquant.strategy.grow_strategy import GrowStrategyHandler


def run_grow_strategy(st, ed):
    strategy: GrowStrategyHandler = GrowStrategyHandler()
    center: SimCenter = SimCenter(strategy, st, ed)
    center.run()


if __name__ == '__main__':
    run_grow_strategy('20190101', '20200123')
