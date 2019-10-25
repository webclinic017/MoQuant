from decimal import Decimal


class ShareHold(object):
    __ts_code: str
    __num: Decimal

    def __init__(self, ts_code, num):
        self.__ts_code = ts_code
        self.__num = num

    def get_ts_code(self):
        return self.__ts_code

    def get_num(self):
        return self.__num
