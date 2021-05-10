from decimal import Decimal

from moquant.simulator.constants import order_status, order_type


class SimOrder(object):
    __msg: str
    __type: int
    __ts_code: str
    __num: int
    __price: Decimal
    __cost: Decimal
    __status: int

    __deal_price: Decimal
    __deal_cost: Decimal

    def __init__(self, t: int, ts_code: str, num: int, price: Decimal, cost: Decimal,
                 success: bool = True, msg: str = ''):
        self.__type = t
        self.__ts_code = ts_code
        self.__num = num
        self.__price = price
        self.__cost = cost
        self.__msg = msg
        self.__status = order_status.sent if success else order_status.fail

    def available(self):
        return self.__status == order_status.sent

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
        return self.__status == order_status.deal

    def get_cost(self):
        return self.__cost

    def is_buy_order(self):
        return self.__type == order_type.buy

    def is_sell_order(self):
        return self.__type == order_type.sell

    def get_deal_price(self):
        return self.__deal_price

    def get_deal_cost(self):
        """
        买入= 买入话费 + 手续费
        卖出= 手续费
        :return: 订单成交的花费
        """
        return self.__deal_cost

    """##################################### update part #####################################"""

    def deal(self, deal_price: Decimal, deal_cost: Decimal):
        """
        成交后更新订单，请勿在handler中调用
        :param deal_price:
        :param deal_cost:
        """
        self.__status = order_status.deal
        self.__deal_price = deal_price
        self.__deal_cost = deal_cost

    def day_pass(self):
        """
        天过去后把旧订单作废，请勿在handler中调用
        """
        self.__status = order_status.outdated

    def retrieve(self):
        """
        撤回订单，请勿在handler中调用
        :return:
        """
        if self.available():
            self.__status = order_status.retrieve
            return True
        return False

    def outdated(self):
        """
        关闭订单，请勿在handler中调用
        :return:
        """
        if self.available():
            self.__status = order_status.outdated
            return True
        return False
