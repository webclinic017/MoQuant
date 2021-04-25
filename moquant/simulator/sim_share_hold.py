from decimal import Decimal

from moquant.utils import decimal_utils


class SimShareHold(object):
    __ts_code: str  # 股票编码
    __holding_num: Decimal  # 持有数量
    __current_price: Decimal  # 当前价格

    __cost: Decimal  # 买入花费
    __win_rate: Decimal  # 止盈线
    __lose_rate: Decimal  # 止损线
    __can_trade: bool  # 是否可以交易
    __on_sell: Decimal  # 在售数量

    def __init__(self, ts_code, num, current_price: Decimal, buy_cost: Decimal,
                 win_rate: Decimal = 0.25, lose_rate: Decimal = -0.08):
        self.__ts_code = ts_code
        self.__holding_num = Decimal(num)
        self.__cost = buy_cost
        self.__current_price = Decimal(current_price)
        self.__win_rate = Decimal(win_rate)
        self.__lose_rate = Decimal(lose_rate)
        self.__can_trade = False
        self.__on_sell = Decimal(0)

    def get_ts_code(self):
        return self.__ts_code

    def get_num(self):
        return self.__holding_num

    def get_can_sell(self):
        return self.__holding_num - self.__on_sell

    def get_earn(self):
        """
        当前盈利 = 当前市值 - 买入花费
        :return: 当前盈利
        """
        return self.get_mv() - self.__cost

    def get_cost(self):
        return self.__cost

    def achieve_win(self):
        if self.__win_rate is None:
            return False
        else:
            return self.get_mv() >= self.__cost * (1 + self.__win_rate)

    def achieve_lose(self):
        if self.__lose_rate is None:
            return False
        else:
            return self.get_mv() <= self.__cost * (1 + self.__lose_rate)

    def can_trade(self):
        return self.__can_trade

    def get_mv(self):
        return self.__holding_num * self.__current_price

    def get_current_price(self):
        return self.__current_price

    """##################################### update part #####################################"""

    def sub_cost_for_dividend(self, cash: Decimal):
        """
        分红后降低成本
        :param cash: 拿到的分红钱
        :return:
        """
        self.__cost = decimal_utils.sub(self.__cost, cash)

    def add_dividend_share(self, dividend_num: int):
        """
        增加分红获得的股数，暂时默认当天可交易
        :param dividend_num:
        :return:
        """
        self.__holding_num = self.__holding_num + dividend_num

    def update_after_deal(self, delta_num, cost):
        """
        成交后，更新持股数和买入费用
        :param delta_num:
        :param cost:
        :return:
        """
        self.__holding_num = self.__holding_num + delta_num
        if delta_num < 0:  # 卖出成功，减少在售数量
            self.__on_sell = self.__on_sell + delta_num
        self.__cost = self.__cost + cost

    def clear_unsell(self):
        """
        清空在售数量
        :return:
        """
        self.__on_sell = 0

    def update_price(self, price):
        self.__current_price = price

    def update_can_trade(self, can: bool):
        self.__can_trade = can

    def update_on_sell(self, delta_num):
        self.__on_sell += delta_num
