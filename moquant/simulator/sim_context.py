import math
from decimal import Decimal

from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.simulator.sim_daily_record import SimDailyRecord
from moquant.simulator.sim_data_service import SimDataService
from moquant.simulator.sim_dividend import SimDividend
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_share_price import SimSharePrice
from moquant.utils.datetime import format_delta

log = get_logger(__name__)


class SimContext(object):
    __sd: str
    __ed: str
    __init_cash: Decimal
    __cash: Decimal
    __charge: Decimal
    __tax: Decimal

    __sz: set  # trade date
    __sh: set  # trade date

    __orders: dict
    __cd: str  # current date
    __shares: dict
    __shares_just_buy: dict
    __dividend: dict
    __records: dict

    __data: SimDataService

    def __init__(self, sd: str, ed: str, cash: Decimal = 500000, charge: Decimal = 0.00025,
                 tax: Decimal = 5):
        self.__sd = sd
        self.__ed = ed
        self.__init_cash = Decimal(cash)
        self.__cash = Decimal(cash)
        self.__charge = Decimal(charge)
        self.__tax = Decimal(tax)

        self.__data = SimDataService(sd, ed)

        self.__sz = self.__data.get_sz_trade_cal()
        self.__sh = self.__data.get_sh_trade_cal()

        self.__shares = {}
        self.__shares_just_buy = {}
        self.__dividend = {}
        self.__records = {}
        self.__orders = {}
        self.__price = {}
        self.__dividend = {}

        self.__cd = format_delta(sd, -1)
        # find next trade day
        self.__next_day()

    """##################################### flow part #####################################"""

    def day_init(self):
        self.__merge_yesterday_buy()
        self.__update_for_dividend()

        self.__orders[self.__cd] = []
        self.__price = {}
        daily_info_list: list = self.__data.get_daily_info(self.__cd)

        for (ts_code, share) in self.__shares.items():  # type: str, SimShareHold
            share.update_can_trade(False)

        # Init price info
        for daily in daily_info_list:  # type: TsDailyTradeInfo
            self.__price[daily.ts_code] = SimSharePrice(pre_close=daily.pre_close, open=daily.open, close=daily.close,
                                                        low=daily.low, high=daily.high)
            if daily.ts_code in self.__shares:
                hold: SimShareHold = self.__shares[daily.ts_code]
                hold.update_price(daily.pre_close)
                hold.update_can_trade(True)

        # Update limit
        stk_limit_lit: list = self.__data.get_stk_limit(self.__cd)
        for stk_limit in stk_limit_lit:  # type: TsStkLimit
            if stk_limit.ts_code in self.__price:
                price: SimSharePrice = self.__price[stk_limit.ts_code]
                price.update_limit(stk_limit.up_limit, stk_limit.down_limit)

    def __merge_yesterday_buy(self):
        for (ts_code, share) in self.__shares_just_buy.items():  # type: str, SimShareHold
            if ts_code in self.__shares:
                self.__shares[ts_code].update_after_deal(share.get_num(), share.get_earn(), share.get_cost())
            else:
                self.__shares[ts_code] = share
        self.__shares_just_buy = {}

    # Add cash and share for dividend
    def __update_for_dividend(self):
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
        # update price after trade is closed
        for (ts_code, price) in self.__price.items():  # type: str, SimSharePrice
            if ts_code in self.__shares:
                share: SimShareHold = self.__shares[ts_code]
                share.update_price(price.get_close())
            if ts_code in self.__shares_just_buy:
                share: SimShareHold = self.__shares_just_buy[ts_code]
                share.update_price(price.get_close())

        # clear empty hold
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

        # failure order
        for order in self.__orders[self.__cd]:  # type: SimOrder
            if order.available():
                order.day_pass()
                if order.get_order_type() == 1:  # buy
                    self.__cash = self.__cash + order.get_num() * order.get_price()
                elif order.get_order_type() == 0:  # sell
                    hold: SimShareHold = self.get_hold(order.get_ts_code())
                    if hold is None:
                        self.error('A sell order without share hold')
                    else:
                        hold.update_on_sell(order.get_num() * (-1))

        # register dividend
        dividend_list = self.__data.get_dividend(self.__cd)

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
            self.info('Dividend register. code: %s, num: %s, cash: %s' % (dividend.ts_code, dividend_num, dividend_cash))
        self.__mark_record()
        self.__next_day()

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
        cost = earn * self.__charge + self.__tax
        hold.update_after_deal(order.get_num() * (-1), earn, cost)
        self.__cash = self.__cash + earn - cost
        self.info("Sell %s of %s with price %s." % (order.get_num(), order.get_ts_code(), deal_price))
        order.deal()

    def __deal_buy(self, order: SimOrder, deal_price: Decimal):
        if order.get_order_type() != 1:
            self.error('[deal_buy] Not buy type order')
            return
        ts_code = order.get_ts_code()
        hold: SimShareHold = self.get_hold(ts_code)
        if hold is None:
            self.__shares[ts_code] = SimShareHold(ts_code, order.get_num(), deal_price)
        else:
            hold.update_after_deal(order.get_num(), 0, order.get_num() * deal_price)
        buy_cost = order.get_num() * deal_price
        self.__cash = self.__cash + (order.get_num() * order.get_price()) - buy_cost
        self.info("Buy %s of %s with price %s. Total cost: %s" %
                  (order.get_num(), order.get_ts_code(), deal_price, buy_cost))
        order.deal()

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
            self.info('Send order successfully. type: %d, code: %s' % (order.get_order_type(), order.get_ts_code()))
        else:
            self.warn('Send order fail. type: %d, code: %s, reason: %s' %
                      (order.get_order_type(), order.get_ts_code(), order.get_msg()))

    """##################################### get info part #####################################"""

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