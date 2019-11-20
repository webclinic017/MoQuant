from decimal import Decimal

from moquant.simulator.sim_share_hold import SimShareHold


class SimDailyRecord(object):
    __mv: dict
    __cash: Decimal

    def __init__(self):
        self.__mv = {}
        self.__cash = 0

    def add_share(self, share: SimShareHold):
        if share.get_ts_code() not in self.__mv:
            self.__mv[share.get_ts_code()] = 0
        self.__mv[share.get_ts_code()] += share.get_mv()

    def add_cash(self, cash: Decimal):
        self.__cash += cash

    def get_total(self):
        ret = 0
        for key, value in self.__mv:
            ret += value
        ret += self.__cash
        return ret