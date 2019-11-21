from decimal import Decimal


class SimShareHold(object):
    __ts_code: str
    __num: Decimal
    __price: Decimal
    __cost: Decimal
    __earn: Decimal
    __win_rate: Decimal
    __lose_rate: Decimal
    __trade: bool
    __on_sell: Decimal

    def __init__(self, ts_code, num, current_price: Decimal,
                 win_rate: Decimal = 0.25, lose_rate: Decimal = -0.08):
        self.__ts_code = ts_code
        self.__num = Decimal(num)
        self.__cost = Decimal(current_price) * Decimal(num)
        self.__earn = Decimal(0)
        self.__price = Decimal(current_price)
        self.__win_rate = Decimal(win_rate)
        self.__lose_rate = Decimal(lose_rate)
        self.__can_trade = False
        self.__on_sell = Decimal(0)

    def get_ts_code(self):
        return self.__ts_code

    def get_num(self):
        return self.__num

    def get_can_sell(self):
        return self.__num - self.__on_sell

    def get_earn(self):
        return self.__earn

    def get_net_earn(self):
        return self.__earn - self.__cost

    def get_cost(self):
        return self.__cost

    def achieve_win(self):
        if self.__win_rate is None:
            return False
        else:
            return self.__price * self.__num + self.__earn >= self.__cost * (1 + self.__win_rate)

    def achieve_lose(self):
        if self.__lose_rate is None:
            return False
        else:
            return self.__price * self.__num + self.__earn <= self.__cost * (1 + self.__lose_rate)

    def can_trade(self):
        return self.__can_trade

    def get_mv(self):
        return self.__num * self.__price

    """##################################### update part #####################################"""

    def update_by_dividend(self, cash_div_tax, stk_div):
        self.__price = (self.__price - cash_div_tax) / (1 + stk_div)

    def add_dividend(self, dividend_num):
        self.__num = self.__num + dividend_num

    def update_after_deal(self, delta_num, earn, cost):
        self.__num = self.__num + delta_num
        if delta_num < 0: # sell
            self.__on_sell -= delta_num
        self.__earn = self.__earn + earn
        self.__cost = self.__cost + cost

    def update_price(self, price):
        self.__price = price

    def update_can_trade(self, can: bool):
        self.__can_trade = can

    def update_on_sell(self, delte_num):
        self.__on_sell += delte_num
