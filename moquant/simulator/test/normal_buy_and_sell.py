from decimal import Decimal

from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_center import SimCenter
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_price import SimDailyPrice
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.utils import decimal_utils

log = get_logger(__name__)


class NormalBuyAndSell(SimHandler):
    """
        最简单的买入持有测试
        选了个1元股
        刚好有买入手续费的边界问题
    """
    __target: str = '000587.SZ'
    __buy_order: SimOrder
    __sell_order: SimOrder
    __buy_cost: Decimal
    __sell_cost: Decimal

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        price: SimDailyPrice = context.get_today_price(self.__target)
        s: SimShareHold = context.get_hold(self.__target)

        if context.is_first_day():
            predict_num = context.get_max_can_buy(context.get_cash(), price.pre_close_qfq)
            self.__buy_order = context.buy_amap(self.__target, price.pre_close_qfq)
            # 可买入数量应考虑了手续费
            assert self.__buy_order.get_num() == predict_num

        elif context.is_last_day():
            self.__sell_order = context.sell_share(s.get_ts_code(), s.get_can_sell(), price.pre_close_qfq)

        elif s is not None:
            assert decimal_utils.equals(price.pre_close_qfq, s.get_current_price())

    def before_trade(self, context: SimContext, data: SimDataService):
        price: SimDailyPrice = context.get_today_price(self.__target)
        s: SimShareHold = context.get_hold(self.__target)

        if context.is_first_day():
            # 这天应该能按开盘价成交
            assert self.__buy_order.is_deal()
            assert decimal_utils.equals(self.__buy_order.get_deal_price(), price.open)

            charge: Decimal = context.get_charge()
            pass_t: Decimal = context.get_pass_tax()
            self.__buy_cost: Decimal = (self.__buy_order.get_num() * self.__buy_order.get_deal_price()) * \
                                       (1 + charge + pass_t)
            # 手续费计算验证
            assert decimal_utils.equals(self.__buy_cost, self.__buy_order.get_deal_cost())

        elif context.is_last_day():
            # 这天应该能按开盘价成交
            assert self.__sell_order.is_deal()

            assert decimal_utils.equals(self.__sell_order.get_deal_price(), price.open)

            # 全卖光了
            assert s.get_num() == 0
            assert s.get_can_sell() == 0

            charge: Decimal = context.get_charge()
            pass_t: Decimal = context.get_pass_tax()
            tax: Decimal = context.get_tax()
            self.__sell_cost = (self.__sell_order.get_num() * self.__sell_order.get_deal_price()) * \
                               (charge + pass_t + tax)
            # 手续费计算验证
            assert decimal_utils.equals(self.__sell_cost, self.__sell_order.get_deal_cost())

            earn = self.__sell_order.get_num() * self.__sell_order.get_deal_price()
            assert decimal_utils.equals(context.get_cash(), context.get_init_cash() + earn
                                        - self.__buy_order.get_deal_cost() - self.__sell_order.get_deal_cost())

        elif s is not None:
            assert decimal_utils.equals(price.open, s.get_current_price())

    def after_trade(self, context: SimContext, data: SimDataService):
        price: SimDailyPrice = context.get_today_price(self.__target)
        s: SimShareHold = context.get_hold(self.__target)
        if s is not None:
            assert decimal_utils.equals(price.close, s.get_current_price())


if __name__ == '__main__':
    strategy: NormalBuyAndSell = NormalBuyAndSell()
    center: SimCenter = SimCenter(strategy, '20210108', '20210120')
    center.run()
