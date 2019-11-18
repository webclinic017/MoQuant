import math
from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.simulator.sim_dividend import SimDividend
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_share_price import SimSharePrice
from moquant.tsclient import ts_client
from moquant.utils.datetime import format_delta

log = get_logger('moquant.simulator.SimContext')


class SimContext(object):
    __sd: str
    __ed: str
    __cash: Decimal
    __reserved_cash: Decimal  # money sent out for buying
    __charge: Decimal
    __tax: Decimal

    __sz: set  # trade date
    __sh: set  # trade date

    __orders: dict
    __cd: str  # current date
    __shares: dict
    __dividend: dict
    __records: dict

    def __init__(self, sd: str, ed: str, cash: Decimal = 500000, charge: Decimal = 0.00025,
                 tax: Decimal = 5):
        self.__sd = sd
        self.__ed = ed
        self.__cash = cash
        self.__reserved_cash = 0
        self.__charge = charge
        self.__tax = tax

        sz = ts_client.fetch_trade_cal(exchange='SZSE', start_date=sd, end_date=ed, is_open=1)
        self.__sz = set([i for i in sz['cal_date'].items()])

        sh = ts_client.fetch_trade_cal(exchange='SSE', start_date=sd, end_date=ed, is_open=1)
        self.__sh = set([i for i in sh['cal_date'].items()])

        self.__cd = sd
        self.__shares = {}
        self.__dividend = {}
        self.__records = {}
        self.__orders = {}
        self.__price = {}
        self.__dividend = {}

    def day_init(self):
        self.__update_for_dividend()

        self.__orders[self.__cd] = []
        self.__price = {}
        session: Session = db_client.get_session()
        daily_info_list = session.query(TsDailyTradeInfo).filter(TsDailyTradeInfo.trade_date == self.__cd).all()
        # TODO update share price
        for daily in daily_info_list:  # type: TsDailyTradeInfo
            self.__price[daily.ts_code] = SimSharePrice(pre_close=daily.pre_close, low=daily.low, high=daily.high)
        dividend_list = session.query(TsDividend).filter(
            and_(TsDividend.div_proc == '实施', TsDividend.ex_date == self.__cd)
        ).all()
        for dividend in dividend_list:  # type: TsDividend
            cash_div_tax = dividend.cash_div_tax if dividend.cash_div_tax is not None else 0
            stk_div = dividend.stk_div if dividend.stk_div is not None else 0
            price: SimSharePrice = self.__price[dividend.ts_code]
            if price is not None:
                price.update_by_dividend(cash_div_tax, stk_div)
            share: SimShareHold = self.__shares[dividend.ts_code]
            if share is not None:
                share.update_by_dividend(cash_div_tax, stk_div)

    # Add cash and share for dividend
    def __update_for_dividend(self):
        finish_dividend = set([])
        for ts_code in self.__dividend:
            dividend: SimDividend = self.__dividend[ts_code]
            if dividend.pay_date == self.__cd:
                self.__cash = self.__cash + dividend.dividend_cash
            if dividend.div_listdate == self.__cd:
                share: SimShareHold = self.__shares[ts_code]
                if share is not None:
                    share.add_dividend(dividend.dividend_num)
                else:
                    self.__shares[ts_code] = SimShareHold(ts_code, dividend.dividend_num, 0, 0, 0, 0)
            if dividend.pay_date >= self.__cd and dividend.div_listdate >= self.__cd:
                finish_dividend.add(ts_code)

        # delete finish dividend
        for ts_code in finish_dividend: # type: str
            self.__dividend.pop(ts_code)

    def day_end(self):
        session: Session = db_client.get_session()
        dividend_list = session.query(TsDividend).filter(
            and_(TsDividend.div_proc == '实施', TsDividend.ex_date == self.__cd)
        ).all()
        for dividend in dividend_list:  # type: TsDividend
            share: SimShareHold = self.__shares[dividend.ts_code]
            if share is not None:
                dividend_num = math.floor(math.floor(share.get_num() / 10) * (dividend.stk_div * 10))
                dividend_cash = share.get_num() * dividend.cash_div
                self.__dividend[dividend.ts_code] = SimDividend(dividend.ts_code, dividend_num, dividend_cash,
                                                                dividend.pay_date, dividend.div_listdate)

    def sell_share(self, ts_code: str, num: Decimal = 0, price: Decimal = 0) -> SimOrder:
        order: SimOrder = None
        if num == 0:
            order = SimOrder(0, ts_code, num, price, False, 'You cant sell nothing')

        if ts_code not in self.__shares:
            order = SimOrder(0, ts_code, num, price, False, 'You dont hold any %s' % ts_code)

        share: SimShareHold = self.__shares[ts_code]
        if share.get_num() < num:
            order = SimOrder(0, ts_code, num, price, False, 'You have only %d of %s' % (num, ts_code))

        order = SimOrder(0, ts_code, num, price)
        self.__add_order(order)
        return order

    # Buy share with cash as more as possible
    def buy_amap(self, ts_code: str, price: Decimal, cash: Decimal = None):
        order: SimOrder = None
        if cash is None:
            cash = self.__cash
        elif self.__cash < cash:
            cash = self.__cash

        num = math.floor(cash / (price * 100)) * 100
        total_cost = num * price
        if num == 0:
            order = SimOrder(1, ts_code, num, price, False, 'You cant buy nothing')
        else:
            order = SimOrder(1, ts_code, num, price)
            self.__reserved_cash += total_cost
            self.__cash -= total_cost
        self.__add_order(order)
        return order

    def __add_order(self, order: SimOrder):
        self.__orders[self.__cd].append(order)
        if order.is_sent():
            log.info('Send order successfully. type: %d, code: %s' % (order.get_order_type(), order.get_ts_code()))
        else:
            log.error('Send order fail. type: %d, code: %s' % (order.get_order_type(), order.get_ts_code()))

    def get_holding(self):
        return self.__shares

    def get_dt(self):
        return self.__cd

    def next_date(self):
        if self.__cd == self.__ed:
            return
        self.__cd = format_delta(self.__cd, 1)

    def get_cash(self):
        return self.__cash
