from decimal import Decimal


class SimDailyRecord(object):
    __d: str
    __mv: Decimal

    def __init__(self, d: str, mv: Decimal = 0):
        self.__d = d
        self.__mv = mv
