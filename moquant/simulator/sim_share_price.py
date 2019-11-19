from decimal import Decimal


class SimSharePrice(object):
    __pre_close: Decimal
    __open: Decimal
    __low: Decimal
    __high: Decimal
    __up_limit: Decimal
    __down_limit: Decimal

    def __init__(self, pre_close: Decimal, open: Decimal, low: Decimal, high: Decimal):
        self.__pre_close = pre_close
        self.__open = open
        self.__low = low
        self.__high = high

    def update_by_dividend(self, cash_div_tax, stk_div):
        self.__pre_close = (self.__pre_close - cash_div_tax) / (1 + stk_div)

    def update_limit(self, up_limit: Decimal, down_limit: Decimal):
        self.__up_limit = up_limit
        self.__down_limit = down_limit

    def get_up_limit(self):
        return self.__up_limit

    def get_open(self):
        return self.__open
