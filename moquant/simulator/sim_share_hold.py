from decimal import Decimal


class SimShareHold(object):
    __ts_code: str
    __num: Decimal
    __cost_price: Decimal
    __price: Decimal
    __win_rate: Decimal
    __lose_rate: Decimal
    __win: Decimal
    __lose: Decimal

    def __init__(self, ts_code, num, cost_price: Decimal, current_price: Decimal = None,
                 win_rate: Decimal = 0.25, lose_rate: Decimal = 0.08):
        self.__ts_code = ts_code
        self.__num = num
        self.__cost_price = cost_price
        self.__price = cost_price if current_price is None else current_price
        self.__win_rate = win_rate
        self.__lose_rate = lose_rate

    def get_ts_code(self):
        return self.__ts_code

    def get_num(self):
        return self.__num

    def cal_sell_price(self):
        self.__win = self.__cost_price * (1 + self.__win_rate)
        self.__lose = self.__cost_price * (1 - self.__lose_rate)

    def achieve_win(self):
        if self.__win is None:
            return False
        else:
            return self.__win <= self.__current_price

    def achieve_lose(self):
        if self.__lose is None:
            return False
        else:
            return self.__lose >= self.__current_price

    def update_by_dividend(self, cash_div_tax, stk_div):
        self.__price = (self.__price - cash_div_tax) / (1 + stk_div)

    def add_dividend(self, dividend_num):
        self.__num = self.__num + dividend_num
