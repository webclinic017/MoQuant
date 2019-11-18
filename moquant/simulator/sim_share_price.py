from decimal import Decimal


class SimSharePrice(object):
    __pre_close: Decimal
    __low: Decimal
    __high: Decimal

    def __init__(self, pre_close: Decimal, low: Decimal, high: Decimal):
        self.__pre_close = pre_close
        self.__low = low
        self.__high = high

    def update_by_dividend(self, cash_div_tax, stk_div):
        self.__pre_close = (self.__pre_close - cash_div_tax) / (1 + stk_div)
