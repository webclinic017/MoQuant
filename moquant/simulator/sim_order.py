from decimal import Decimal


class SimOrder(object):
    __msg: str
    __type: int  # 0 sell 1 buy
    __ts_code: str
    __num: int
    __price: Decimal
    __status: int  # 0 sent, 1 deal, -1 rejected, -2 retrieve, -99 not available

    def __init__(self, type: int, ts_code: str, num: int, price: Decimal, success: bool = True, msg: str = ''):
        self.__type = type
        self.__ts_code = ts_code
        self.__num = num
        self.__price = price
        self.__msg = msg
        self.__status = 0 if success else -1

    def available(self):
        return self.__status == 0

    def get_order_type(self):
        return self.__type

    def get_ts_code(self):
        return self.__ts_code

    def get_price(self):
        return self.__price

    def get_num(self):
        return self.__num

    def get_msg(self):
        return self.__msg

    def is_deal(self):
        return self.__status == 1

    """##################################### update part #####################################"""

    def deal(self):
        self.__status = 1

    def day_pass(self):
        self.__status = -99
