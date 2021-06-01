import math
from decimal import Decimal

from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.simulator.constants import order_type
from moquant.simulator.sim_daily_price import SimDailyPrice
from moquant.simulator.sim_dividend import SimDividend
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.utils.date_utils import format_delta
from moquant.simulator.data import SimDataService

log = get_logger(__name__)


class SimContext(object):
    def __init__(self, ds: SimDataService, sd: str, ed: str, cash: Decimal = 500000,
                 charge: Decimal = 0.00025, tax: Decimal = 0.001, pass_tax: Decimal = 0.00002):
        """
        :param ds: 获取数据服务
        :param sd: 回测开始日期
        :param ed: 回测结束日期
        :param cash: 起始现金
        :param charge: 交易费率 - 券商佣金
        :param tax: 印花税率
        :param pass_tax: 过户费率
        """
        self.__sd = sd  # 回测开始日期
        self.__ed = ed  # 回测结束日期
        self.__init_cash = Decimal(cash)  # 初始现金
        self.__cash = Decimal(cash)  # 现金
        self.__charge = Decimal(charge)  # 交易费率 - 券商佣金
        self.__tax = Decimal(tax)  # 印花税率
        self.__pass = Decimal(pass_tax)  # 过户费率

        self.__data = ds
        self.__sz, self.__sh = ds.get_trade_calendar(sd, ed)  # 深沪市交易日历

        self.__shares = {}  # 拥有的股票
        self.__shares_just_buy = {}  # 当日买的股票
        self.__dividend = {}  # 登记了分红送股的
        self.__records = {}  #
        self.__orders = {}  # 订单
        self.__price = {}  # 每日价格信息，只保存当天的

        self.__cd = format_delta(sd, -1)  # 当前日期
        self.next_day()  # 进入下一个交易日
        self.info('Ready for simulation')

        self.__register_code = set()
        self.__inited = False

    def register_code(self, ts_code_set):
        if self.__inited:
            raise Exception('Can only register code during init')
        for i in ts_code_set:
            self.__register_code.add(i)

    def __with_cache(self):
        return len(self.__register_code) > 0

    def finish_init(self):
        self.__inited = True
        if not self.__with_cache():
            return
        self.__data.init_cache(self.__register_code, self.__sd, self.__ed)


    """##################################### flow part #####################################"""

    def day_init(self):
        self.__merge_yesterday_buy()
        self.__update_for_dividend()
        self.__fetch_today_price()
        self.__update_price_to_pre_close()

    def __merge_yesterday_buy(self):
        """
        把前一天买的票合并到可卖列表中
        """
        for (ts_code, share) in self.__shares_just_buy.items():  # type: str, SimShareHold
            if ts_code in self.__shares:
                self.__shares[ts_code].update_after_deal(share.get_num(), share.get_cost())
            else:
                self.__shares[ts_code] = share
        self.__shares_just_buy = {}

    def __update_for_dividend(self):
        """
        处理分红
        """
        finish_dividend = set([])
        for ts_code in self.__dividend:
            dividend: SimDividend = self.__dividend[ts_code]
            if dividend.ex_date == self.__cd:
                self.info('Get dividend cash. code: %s, cash: %s' % (dividend.ts_code, dividend.dividend_cash))
                self.__cash = self.__cash + dividend.dividend_cash
                if ts_code in self.__shares:
                    share: SimShareHold = self.__shares[ts_code]
                    share.sub_cost_for_dividend(dividend.dividend_num)
            if dividend.div_listdate == self.__cd:
                self.info('Get dividend share. code: %s, num: %s' % (dividend.ts_code, dividend.dividend_num))
                if ts_code in self.__shares:
                    share: SimShareHold = self.__shares[ts_code]
                    share.add_dividend_share(dividend.dividend_num)
                else:
                    self.__shares[ts_code] = SimShareHold(ts_code, dividend.dividend_num, 0)
            if dividend.finish(self.__cd):
                finish_dividend.add(ts_code)

        # delete finish dividend
        for ts_code in finish_dividend:  # type: str
            self.__dividend.pop(ts_code)

    def __fetch_today_price(self):
        """
        获取当天所有股票的价格信息，只保存当天
        :return:
        """
        self.__price = {}
        price_list: list = self.__data.get_price_between(ts_code_arr=None, now_date=self.__cd,
                                                         from_date=self.__cd, to_date=self.__cd, adj_type='')
        for p in price_list:  # type: SimDailyPrice
            self.__price[p.ts_code] = p

    def __update_price_to_pre_close(self):
        """
        更新股票价格到前一个交易日收盘价，前复权
        :return:
        """
        for (ts_code, hold) in self.__shares.items():  # type: str, SimShareHold
            price: SimDailyPrice = self.get_today_price(ts_code)
            if price is not None:
                hold.update_price(price.pre_close)

    def deal_after_morning_auction(self):
        """
        早盘竞价后成交，仅需要判断开盘价
        :return:
        """
        order_list: list = self.get_today_orders()
        for order in order_list:  # type: SimOrder
            if not order.available():
                continue
            price: SimDailyPrice = self.get_today_price(order.get_ts_code())
            if order.is_sell_order():
                if order.get_price() < price.open:
                    self.__deal_sell(order, price.open)
            elif order.is_buy_order():
                if order.get_price() > price.open:
                    self.__deal_buy(order, price.open)
        self.__update_price_to_open()

    def __update_price_to_open(self):
        for (ts_code, hold) in self.__shares.items():  # type: str, SimShareHold
            price: SimDailyPrice = self.get_today_price(ts_code)
            if price is not None:
                hold.update_price(price.open)

    def deal_after_afternoon_auction(self):
        order_list: list = self.get_today_orders()
        for order in order_list:  # type: SimOrder
            if not order.available():
                continue
            price: SimDailyPrice = self.get_today_price(order.get_ts_code())
            if order.is_sell_order():
                if order.get_price() < price.high:
                    self.__deal_sell(order,
                                     order.get_price() if order.get_price() > price.low else price.low)
            elif order.is_buy_order():
                if order.get_price() > price.low:
                    self.__deal_buy(order,
                                    order.get_price() if order.get_price() < price.high else price.high)

    def day_end(self):
        """
        交易日结束
        """
        self.__clear_empty_hold()
        self.__update_price_to_close()
        self.__close_order()
        self.__register_dividend()

    def __close_order(self):
        """
        关闭没成交的订单
        目前仅删除所有订单记录
        将持股在售数量归零
        将未买入现金归还
        :return:
        """
        if self.__cd not in self.__orders:
            return
        for o in self.__orders[self.__cd]:  # type: SimOrder
            r: bool = o.outdated()
            if r:
                self.__revert_from_order(o)

    def __register_dividend(self):
        """
        根据持股登记分红配股
        """
        dividend_list = self.__data.get_dividend_in_record_day(self.__cd)
        for dividend in dividend_list:  # type: TsDividend
            total_num = 0
            if dividend.ts_code in self.__shares:
                share: SimShareHold = self.__shares[dividend.ts_code]
                total_num = total_num + share.get_num()
            if dividend.ts_code in self.__shares_just_buy:
                share: SimShareHold = self.__shares_just_buy[dividend.ts_code]
                total_num = total_num + share.get_num()

            if total_num == 0:
                continue
            dividend_num = math.floor(math.floor(total_num / 10) * (dividend.stk_div * 10))
            dividend_cash = total_num * dividend.cash_div
            self.__dividend[dividend.ts_code] = SimDividend(dividend.ts_code, dividend_num, dividend_cash,
                                                            dividend.ex_date, dividend.div_listdate)
            self.info('Dividend register. code: %s, num: %s, cash: %s' %
                      (dividend.ts_code, dividend_num, dividend_cash))

    def __update_price_to_close(self):
        """
        每天结束后更新价格到收盘价
        """
        for (ts_code, price) in self.__price.items():  # type: str, SimDailyPrice
            if ts_code in self.__shares:
                share: SimShareHold = self.__shares[ts_code]
                share.update_price(price.close)
            if ts_code in self.__shares_just_buy:
                share: SimShareHold = self.__shares_just_buy[ts_code]
                share.update_price(price.close)

    def __clear_empty_hold(self):
        """
        清空今天已经卖光的股票
        """
        to_clear: set = set()
        for (ts_code, share) in self.__shares.items():  # type: str, SimShareHold
            if share.get_num() != 0:
                continue
            if ts_code not in self.__shares_just_buy:
                to_clear.add(ts_code)
        for ts_code in to_clear:  # type: str
            share: SimShareHold = self.__shares[ts_code]
            self.info("Finish trade of %s, earn %.2f" % (share.get_ts_code(), share.get_earn()))
            self.__shares.pop(ts_code)

    def next_day(self):
        if self.__cd > self.__ed:
            return
        self.__cd = format_delta(self.__cd, 1)
        if self.__cd not in self.__sz and self.__cd not in self.__sh:
            self.next_day()

    def is_first_day(self):
        """
        :return: 是否第一天
        """
        return self.__cd == self.__sd

    def is_last_day(self):
        """
        :return: 是否最后一天
        """
        return self.__cd == self.__ed

    def is_finish(self):
        """
        是否回测结束
        """
        return self.__cd > self.__ed

    """##################################### deal part #####################################"""

    def __deal_sell(self, order: SimOrder, deal_price: Decimal):
        """
        卖出成交
        1. 计算手续费
        2. 增加现金
        3. 减少持股数量
        4. 更新订单状态
        :param order: 卖出订单
        :param deal_price: 成交价格
        """
        if not order.is_sell_order():
            raise Exception('Not a sell order %s' % order)
            return
        ts_code = order.get_ts_code()
        hold: SimShareHold = self.__shares[ts_code] if ts_code in self.__shares else None
        if hold is None:
            self.error('[deal_sell] not holding %s' % ts_code)
            return
        earn = order.get_num() * deal_price
        deal_cost = self.__get_total_sell_cost(earn)
        net_earn = earn - deal_cost
        self.info("Sell %s of %s with price %.2f. Tax: %.2f. Profit: %.2f" %
                  (order.get_num(), order.get_ts_code(), deal_price, deal_cost, net_earn - hold.get_cost()))

        hold.update_after_deal(order.get_num() * (-1), -net_earn)
        self.__cash = self.__cash + net_earn
        order.deal(deal_price, deal_cost)

    def __deal_buy(self, order: SimOrder, deal_price: Decimal):
        """
        买入成交
        1. 计算总费用
        2. 回退未使用金额
        3. 增加持股
        4. 更新订单状态
        :param order: 买入订单
        :param deal_price:
        :return:
        """
        if not order.is_buy_order():
            raise Exception('Not a buy order %s' % order)
        ts_code = order.get_ts_code()
        hold: SimShareHold = self.get_hold(ts_code)
        buy_cost = order.get_num() * deal_price
        deal_cost = self.__get_deal_buy_cost(buy_cost)
        total_buy_cost = buy_cost + deal_cost
        if hold is None:
            hold = SimShareHold(ts_code, order.get_num(), deal_price, total_buy_cost)
            self.__shares[ts_code] = hold
        else:
            hold.update_after_deal(order.get_num(), total_buy_cost)

        self.__cash = self.__cash + order.get_cost() - total_buy_cost
        self.info("Buy %s of %s with price %s. Pay cost: %s. Deal cost: %s" %
                  (order.get_num(), order.get_ts_code(), deal_price, buy_cost, deal_cost))

        order.deal(deal_price, total_buy_cost)

    def __get_tax_cost(self, deal):
        return deal * self.__tax

    def __get_charge_cost(self, deal):
        cost = deal * self.__charge
        if cost < 5:
            cost = 5
        return Decimal(cost)

    def __get_pass_cost(self, deal):
        return deal * self.__pass

    def __revert_from_order(self, order: SimOrder):
        """
        订单过期或者撤回后，进行相应更新
        :param order: 委托订单
        :return:
        """
        if order.is_buy_order():
            self.__cash += order.get_cost()
        elif order.is_sell_order():
            sell: SimShareHold = self.get_hold(order.get_ts_code())
            sell.retrieve_sell(order.get_num())

    """##################################### send order part #####################################"""

    def sell_share(self, ts_code: str, price: Decimal, num: Decimal = None) -> SimOrder:
        """
        按价格卖出
        :param ts_code: 股票编码，不可为空
        :param num: 卖出数量，为空时默认全部卖出
        :param price: 卖出价格，不可为空
        :return: 卖出订单
        """
        order: SimOrder = None
        msg: str = None
        if not self.__can_trade(ts_code):
            msg = 'Cant trade %s in %s' % (ts_code, self.__cd)
        elif ts_code not in self.__price:
            msg = 'Cant find price of %s' % ts_code
            self.error(msg)
        elif self.__price[ts_code].is_trade == 0:
            msg = '%s is in suspension' % ts_code
        elif ts_code not in self.__shares:
            msg = 'You dont hold any %s' % ts_code
        else:
            share: SimShareHold = self.__shares[ts_code]
            if num is None:
                num = share.get_can_sell()
            if share.get_can_sell() < num:
                msg = 'You have only %d of %s that can be sold' % (share.get_can_sell(), ts_code)
            elif num == 0:
                msg = 'You cant sell nothing'
            else:
                order = self.__gen_sell_order(ts_code, price, num)

        if msg is not None:
            order = SimOrder(0, ts_code, num, price, 0, False, msg)
        self.__add_order(order)
        return order

    # Buy share with cash as more as possible
    def buy_amap(self, ts_code: str, price: Decimal, cash: Decimal = None) -> SimOrder:
        """
        按照金额、价格尽量购买，会算入手续费
        :param ts_code: 买入股票
        :param price: 买入价格
        :param cash: 所用资金
        :return: 下单结果
        """
        order: SimOrder = None
        msg: str = None
        if cash is None:
            cash = self.__cash
        elif self.__cash < cash:
            cash = self.__cash

        num = self.get_max_can_buy(cash, price)

        if not self.__can_trade(ts_code):
            msg = 'Cant trade %s in %s' % (ts_code, self.__cd)
        elif ts_code not in self.__price:
            msg = 'Cant find price of %s' % ts_code
            self.error(msg)
        elif self.__price[ts_code].is_trade == 0:
            msg = '%s is suspended' % ts_code
        elif num == 0:
            msg = 'You cant buy anything'

        if msg is None:
            order: SimOrder = self.__gen_buy_order(ts_code, price, num)
            self.__cash -= order.get_cost()
        else:
            order = SimOrder(1, ts_code, num, price, 0, False, msg)
        self.__add_order(order)
        return order

    def __gen_buy_order(self, ts_code: str, price: Decimal, num: int):
        """
        生成买入订单
        :param ts_code: 股票编码
        :param price: 买入价格
        :param num: 买入数量
        :return: 买入订单
        """
        buy_cost: Decimal = num * price
        total_buy_cost = self.__get_total_buy_cost(buy_cost)
        return SimOrder(order_type.buy, ts_code, num, price, total_buy_cost)

    def __get_total_buy_cost(self, buy_cost: Decimal) -> Decimal:
        """
        根据买入金额获取买入总费用
        :param buy_cost: 纯股票买入金额
        :return: 总费用 = 纯股票买入金额 + 手续费
        """
        deal_cost = self.__get_deal_buy_cost(buy_cost)
        return buy_cost + deal_cost

    def __get_deal_buy_cost(self, buy_cost: Decimal):
        """
        买入手续费
        :param buy_cost: 纯股票买入金额
        :return: 手续费 = 佣金 + 过户费
        """
        return self.__get_charge_cost(buy_cost) + self.__get_pass_cost(buy_cost)

    def __gen_sell_order(self, ts_code: str, price: Decimal, num: int):
        """
        生成卖出订单
        :param ts_code: 股票编码
        :param price: 卖出价格
        :param num: 卖出数量
        :return: 卖出订单
        """
        earn: Decimal = num * price
        return SimOrder(order_type.sell, ts_code, num, price, self.__get_total_sell_cost(earn))

    def __get_total_sell_cost(self, buy_cost: Decimal) -> Decimal:
        """
        根据卖出金额获取卖出总费用
        手续费 = 佣金 + 过户费 + 印花税
        :param buy_cost: 股票卖出金额
        :return: 总费用 = 手续费
        """
        return self.__get_charge_cost(buy_cost) + self.__get_pass_cost(buy_cost) + self.__get_tax_cost(buy_cost)

    def get_max_can_buy(self, cash: Decimal, price: Decimal) -> int:
        """
        获取最大可买数量，包括手续费
        :param cash: 可用现金
        :param price: 买入价格
        :return: 可买数量
        """
        return math.floor(cash / (1 + self.__charge + self.__pass) / (price * 100)) * 100

    def __can_trade(self, ts_code: str) -> bool:
        if ts_code.endswith('.SZ') and self.__cd not in self.__sz:
            return False
        if ts_code.endswith('.SH') and self.__cd not in self.__sh:
            return False
        return True

    def __add_order(self, order: SimOrder):
        if self.__cd not in self.__orders:
            self.__orders[self.__cd] = []
        self.__orders[self.__cd].append(order)
        if order.available():
            self.info('Send order successfully. type: %d, code: %s, price: %.2f' %
                      (order.get_order_type(), order.get_ts_code(), order.get_price()))
            if order.is_sell_order():
                ts_code = order.get_ts_code()
                share: SimShareHold = self.__shares[ts_code]
                if ts_code not in self.__shares:
                    raise Exception('No holding of %s' % ts_code)
                share.update_on_sell(order.get_num())
        else:
            self.warn('Send order fail. type: %d, code: %s, reason: %s' %
                      (order.get_order_type(), order.get_ts_code(), order.get_msg()))

    def retrieve_order(self, order: SimOrder):
        """
        撤回取消订单
        :param order:
        :return:
        """
        ret: bool = order.retrieve()
        if ret:
            log.info("Retrieve order. type: %d, code: %s, price: %.2f'" %
                     (order.get_order_type(), order.get_ts_code(), order.get_price()))
            self.__revert_from_order(order)
        return ret

    """##################################### get info part #####################################"""

    def get_charge(self):
        """
        :return: 佣金比例
        """
        return self.__charge

    def get_tax(self):
        """
        :return: 印花税率
        """
        return self.__tax

    def get_pass_tax(self):
        """
        :return: 过户税率
        """
        return self.__pass

    def get_simulate_period(self):
        return self.__sd, self.__ed

    def get_holding(self) -> dict:
        return self.__shares

    def get_hold(self, ts_code) -> SimShareHold:
        return self.__shares[ts_code] if ts_code in self.__shares else None

    def get_dt(self):
        return self.__cd

    def get_init_cash(self):
        return self.__init_cash

    def get_cash(self):
        return self.__cash

    def get_holding_just_buy(self) -> dict:
        return self.__shares_just_buy

    def get_today_price(self, ts_code) -> SimDailyPrice:
        return self.__price[ts_code] if ts_code in self.__price else None

    def get_daily_records(self):
        return self.__records

    def get_today_orders(self):
        return self.__orders[self.__cd] if self.__cd in self.__orders else []

    """##################################### log part #####################################"""

    def info(self, msg: str):
        log.info("[%s] %s" % (self.__cd, msg))

    def warn(self, msg: str):
        log.warn("[%s] %s" % (self.__cd, msg))

    def error(self, msg: str):
        log.error("[%s] %s" % (self.__cd, msg))
