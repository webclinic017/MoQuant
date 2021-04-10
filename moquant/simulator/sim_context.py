import math
from decimal import Decimal

from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.simulator.sim_daily_record import SimDailyRecord
from moquant.simulator.sim_dividend import SimDividend
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_share_price import SimSharePrice
from moquant.utils.date_utils import format_delta
from simulator.data import SimDataService

log = get_logger(__name__)


class SimContext(object):
    def __init__(self,
                 ds: dict(type=SimDataService, help="获取数据服务"),
                 sd: dict(type=str, help="回测开始日期"),
                 ed: dict(type=str, help="回测结束日期"),
                 cash: dict(type=Decimal, help="起始现金") = 500000,
                 charge: dict(type=Decimal, help="交易费率") = 0.00025,
                 tax: dict(type=Decimal, help="印花税率") = 0.001,
                 pass_tax: dict(type=Decimal, help="过户费率") = 0.00002):
        self.__sd = sd  # 回测开始日期
        self.__ed = ed  # 回测结束日期
        self.__init_cash = Decimal(cash)  # 初始现金
        self.__cash = Decimal(cash)  # 现金
        self.__charge = Decimal(charge)  # 交易费率
        self.__tax = Decimal(tax)  # 印花税率
        self.__pass = Decimal(pass_tax)  # 过户费率

        self.__sz = ds.get_sz_trade_cal()  # 深市交易日历
        self.__sh = ds.get_sh_trade_cal()  # 沪市交易日历

        self.__shares = {}  # 拥有的股票
        self.__shares_just_buy = {}  # 当日买的股票
        self.__dividend = {}  # 登记了分红送股的
        self.__records = {}  #
        self.__orders = {}  # 订单

        self.__cd = format_delta(sd, -1)  # 当前日期
        self.__next_day()  # 进入下一个交易日

    """##################################### flow part #####################################"""

    def day_init(self):
        self.__merge_yesterday_buy()
        self.__update_for_dividend()

    def __merge_yesterday_buy(self):
        """
        把前一天买的票合并到可卖列表中
        """
        for (ts_code, share) in self.__shares_just_buy.items():  # type: str, SimShareHold
            if ts_code in self.__shares:
                self.__shares[ts_code].update_after_deal(share.get_num(), share.get_earn(), share.get_cost())
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
            if dividend.pay_date == self.__cd:
                self.info('Get dividend cash. code: %s, cash: %s' % (dividend.ts_code, dividend.dividend_cash))
                self.__cash = self.__cash + dividend.dividend_cash
            if dividend.div_listdate == self.__cd:
                self.info('Get dividend share. code: %s, num: %s' % (dividend.ts_code, dividend.dividend_num))
                if ts_code in self.__shares:
                    share: SimShareHold = self.__shares[ts_code]
                    share.add_dividend(dividend.dividend_num)
                else:
                    self.__shares[ts_code] = SimShareHold(ts_code, dividend.dividend_num, 0)
            if dividend.finish(self.__cd):
                finish_dividend.add(ts_code)

        # delete finish dividend
        for ts_code in finish_dividend:  # type: str
            self.__dividend.pop(ts_code)

    def deal_after_morning_auction(self):
        order_list: list = self.__orders[self.__cd]
        for order in order_list:  # type: SimOrder
            if not order.available():
                continue
            price: SimSharePrice = self.get_price(order.get_ts_code())
            if order.get_order_type() == 0:
                if order.get_price() < price.get_open():
                    self.__deal_sell(order, price.get_open())
            elif order.get_order_type() == 1:
                if order.get_price() > price.get_open():
                    self.__deal_buy(order, price.get_open())
        self.__update_price_to_open()

    def __update_price_to_open(self):
        for (ts_code, hold) in self.__shares.items():  # type: str, SimShareHold
            price: SimSharePrice = self.get_price(ts_code)
            if price is not None:
                hold.update_price(price.get_open())

    def deal_after_afternoon_auction(self):
        order_list: list = self.__orders[self.__cd]
        for order in order_list:  # type: SimOrder
            if not order.available():
                continue
            price: SimSharePrice = self.get_price(order.get_ts_code())
            if order.get_order_type() == 0:
                if order.get_price() < price.get_high():
                    self.__deal_sell(order,
                                     order.get_price() if order.get_price() > price.get_low() else price.get_low())
            elif order.get_order_type() == 1:
                if order.get_price() > price.get_low():
                    self.__deal_buy(order,
                                    order.get_price() if order.get_price() < price.get_high() else price.get_high())

    def day_end(self):
        """
        交易日结束
        """
        self.__update_price_to_close()
        self.__orders.pop(self.__cd, None)
        self.__register_dividend()
        self.__mark_record()
        self.__next_day()

    def __register_dividend(self,
                            ds: dict(type=SimDataService, help="获取数据服务")):
        """
        根据持股登记分红配股
        """
        dividend_list = ds.get_dividend(self.__cd)
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
                                                            dividend.pay_date, dividend.div_listdate)
            self.info(
                'Dividend register. code: %s, num: %s, cash: %s' % (dividend.ts_code, dividend_num, dividend_cash))

    def __update_price_to_close(self):
        """
        每天结束后更新价格到收盘价
        """
        for (ts_code, price) in self.__price.items():  # type: str, SimSharePrice
            if ts_code in self.__shares:
                share: SimShareHold = self.__shares[ts_code]
                share.update_price(price.get_close())
            if ts_code in self.__shares_just_buy:
                share: SimShareHold = self.__shares_just_buy[ts_code]
                share.update_price(price.get_close())

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
            self.info("Finish trade of %s, earn %s" % (share.get_ts_code(), share.get_net_earn()))
            self.__shares.pop(ts_code)

    def __mark_record(self):
        record = SimDailyRecord()
        for (ts_code, share) in self.__shares.items():  # type: str, SimShareHold
            record.add_share(share)
        for (ts_code, share) in self.__shares_just_buy.items():  # type: str, SimShareHold
            record.add_share(share)
        record.add_cash(self.__cash)
        self.__records[self.__cd] = record
        self.info("Market value. cash: %s. share: %s" % (record.get_cash(), record.get_share_value()))

    def __next_day(self):
        if self.__cd > self.__ed:
            return
        self.__cd = format_delta(self.__cd, 1)
        if self.__cd not in self.__sz and self.__cd not in self.__sh:
            self.__next_day()

    def is_finish(self):
        """
        是否回测结束
        """
        return self.__cd > self.__ed

    """##################################### deal part #####################################"""

    def __deal_sell(self, order: SimOrder, deal_price: Decimal):
        if order.get_order_type() != 0:
            self.error('[deal_sell] Not sell type order')
            return
        ts_code = order.get_ts_code()
        hold: SimShareHold = self.__shares[ts_code] if ts_code in self.__shares else None
        if hold is None:
            self.error('[deal_sell] not holding %s' % ts_code)
            return
        earn = order.get_num() * deal_price
        charge_cost = self.__get_charge_cost(earn)
        pass_cost = self.__get_pass_cost(order.get_num())
        tax_cost = self.__get_tax_cost(earn)
        deal_cost = charge_cost + pass_cost + tax_cost
        hold.update_after_deal(order.get_num() * (-1), earn, deal_cost)
        self.__cash = self.__cash + earn - deal_cost
        self.info(
            "Sell %s of %s with price %s. Tax: %s" % (order.get_num(), order.get_ts_code(), deal_price, deal_cost))
        order.deal()

    def __deal_buy(self, order: SimOrder, deal_price: Decimal):
        if order.get_order_type() != 1:
            self.error('[deal_buy] Not buy type order')
            return
        ts_code = order.get_ts_code()
        hold: SimShareHold = self.get_hold(ts_code)
        buy_cost = order.get_num() * deal_price
        charge_cost = self.__get_charge_cost(buy_cost)
        pass_cost = self.__get_pass_cost(buy_cost)
        deal_cost = charge_cost + pass_cost
        if hold is None:
            hold = SimShareHold(ts_code, order.get_num(), deal_price)
            self.__shares[ts_code] = hold
            hold.update_after_deal(0, 0, deal_cost)
        else:
            hold.update_after_deal(order.get_num(), 0, buy_cost + deal_cost)

        self.__cash = self.__cash + (order.get_num() * order.get_price()) - buy_cost
        self.info("Buy %s of %s with price %s. Pay cost: %s. Deal cost: %s" %
                  (order.get_num(), order.get_ts_code(), deal_price, buy_cost, deal_cost))
        order.deal()

    def __get_tax_cost(self, deal):
        return deal * self.__tax

    def __get_charge_cost(self, deal):
        cost = deal * self.__charge
        if cost < 5:
            cost = 5
        return Decimal(cost)

    def __get_pass_cost(self, deal):
        return deal * self.__pass

    """##################################### send order part #####################################"""

    def sell_share(self, ts_code: str, num: Decimal = 0, price: Decimal = 0) -> SimOrder:
        order: SimOrder = None
        msg: str = None
        if not self.__can_trade(ts_code):
            msg = 'Cant trade %s in %s' % (ts_code, self.__cd)
        elif ts_code not in self.__price:
            msg = '%s is in suspension' % ts_code
        elif num == 0:
            msg = 'You cant sell nothing'
        elif ts_code not in self.__shares:
            msg = 'You dont hold any %s' % ts_code
        else:
            share: SimShareHold = self.__shares[ts_code]
            if share.get_can_sell() < num:
                msg = 'You have only %d of %s that can be sold' % (share.get_can_sell(), ts_code)
            else:
                order = SimOrder(0, ts_code, num, price)
                share.update_on_sell(num)

        if msg is not None:
            order = SimOrder(0, ts_code, num, price, False, msg)
        self.__add_order(order)
        return order

    # Buy share with cash as more as possible
    def buy_amap(self, ts_code: str, price: Decimal, cash: Decimal = None):
        order: SimOrder = None
        msg: str = None
        if cash is None:
            cash = self.__cash
        elif self.__cash < cash:
            cash = self.__cash

        num = math.floor(cash / (price * 100)) * 100
        total_cost = num * price
        if not self.__can_trade(ts_code):
            msg = 'Cant trade %s in %s' % (ts_code, self.__cd)
        elif ts_code not in self.__price:
            msg = '%s is in suspension' % ts_code
        elif num == 0:
            msg = 'You cant buy nothing'

        if msg is None:
            order = SimOrder(1, ts_code, num, price)
            self.__cash -= total_cost
        else:
            order = SimOrder(1, ts_code, num, price, False, msg)
        self.__add_order(order)
        return order

    def __can_trade(self, ts_code: str) -> bool:
        if ts_code.endswith('.SZ') and self.__cd not in self.__sz:
            return False
        if ts_code.endswith('.SH') and self.__cd not in self.__sh:
            return False
        return True

    def __add_order(self, order: SimOrder):
        self.__orders[self.__cd].append(order)
        if order.available():
            self.info('Send order successfully. type: %d, code: %s, price: %s' % (
            order.get_order_type(), order.get_ts_code(), order.get_price()))
        else:
            self.warn('Send order fail. type: %d, code: %s, reason: %s' %
                      (order.get_order_type(), order.get_ts_code(), order.get_msg()))

    """##################################### get info part #####################################"""

    def get_simulate_period(self):
        return self.__sd, self.__ed

    def get_holding(self):
        return self.__shares

    def get_hold(self, ts_code):
        return self.__shares[ts_code] if ts_code in self.__shares else None

    def get_dt(self):
        return self.__cd

    def get_cash(self):
        return self.__cash

    def get_price(self, ts_code) -> SimSharePrice:
        return self.__price[ts_code] if ts_code in self.__price else None

    def get_daily_records(self):
        return self.__records

    def analyse(self):
        self.info('-------------------Analyse start-------------------')
        d = self.__sd
        max_mv = self.__init_cash
        last_mv = self.__init_cash
        max_retrieve = 0
        while d <= self.__ed:
            if d in self.__records:
                record: SimDailyRecord = self.__records[d]
                mv = record.get_total()
                if mv > max_mv:
                    max_mv = mv
                last_mv = mv
                retrieve = (max_mv - last_mv) / max_mv
                if retrieve > max_retrieve:
                    max_retrieve = retrieve
            d = format_delta(d, 1)
        self.info('Final market value is %s' % last_mv)
        self.info('Max retrieve: %s' % max_retrieve)

    """##################################### log part #####################################"""

    def info(self, msg: str):
        log.info("[%s] %s" % (self.__cd, msg))

    def warn(self, msg: str):
        log.warn("[%s] %s" % (self.__cd, msg))

    def error(self, msg: str):
        log.error("[%s] %s" % (self.__cd, msg))
