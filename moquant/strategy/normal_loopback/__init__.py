import os

import pandas as pd

from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_center import SimCenter
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_price import SimDailyPrice
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.strategy.normal_loopback.nomral_loopback_share import NormalLoopbackShare

log = get_logger(__name__)


class NormalLoopback(SimHandler):

    def __init__(self, share_list: list):
        self.__dt_map = {}
        self.__list = share_list

        for i in self.__list:  # type: NormalLoopbackShare
            if i.dt not in self.__dt_map:
                self.__dt_map[i.dt] = []
            self.__dt_map[i.dt].append(i)

    def init(self, context: SimContext, data: SimDataService):
        ts_code_set: set = set()
        for i in self.__list:  # type: NormalLoopbackShare
            ts_code_set.add(i.ts_code)
        context.register_code(ts_code_set)

    def morning_auction(self, context: SimContext, data: SimDataService):
        dt: str = context.get_dt()
        if dt not in self.__dt_map:
            return

        shares: dict = context.get_holding()
        for (ts_code, share) in shares.items():  # type: str, SimShareHold
            p: SimDailyPrice = context.get_today_price(ts_code)
            context.sell_share(ts_code, p.down_limit)

    def before_trade(self, context: SimContext, data: SimDataService):
        dt: str = context.get_dt()
        if dt not in self.__dt_map:
            return
        to_buy: list = self.__dt_map[dt]
        # 尽量等权买入
        for i in range(len(to_buy)):
            max_num = len(to_buy) - i
            ts_code = to_buy[i].ts_code
            p: SimDailyPrice = context.get_today_price(ts_code)
            context.buy_amap(ts_code, p.open, context.get_cash() / max_num)

    def after_trade(self, context: SimContext, data: SimDataService):
        pass


def run(from_dt: str = '20210506', to_dt: str = '20210528'):
    module_path = os.path.dirname(__file__)
    file_path = os.path.join(module_path, 'data.csv')
    d = pd.read_csv(file_path)
    share_list: list = []
    for index, row in d.iterrows():
        share_list.append(NormalLoopbackShare(row['ts_code'], str(int(row['dt']))))

    strategy = NormalLoopback(share_list)
    center: SimCenter = SimCenter(strategy, from_dt, to_dt)
    center.run()


if __name__ == '__main__':
    run()
