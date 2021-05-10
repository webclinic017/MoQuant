from moquant.constants import mq_daily_metric_enum
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_center import SimCenter
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_price import SimDailyPrice
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.utils import date_utils

log = get_logger(__name__)


class DownGapN(SimHandler):

    def __init__(self, from_dt: str = '20210218', to_dt: str = '20210507', standard_gap_num: int = 3):
        self.from_dt = from_dt
        self.to_dt = to_dt
        self.standard_gap_num = standard_gap_num

        self.target: set = set()
        self.gap: dict = {}
        self.last_trade_price: dict = {}  # 上一个交易日
        self.yesterday_buy: set = set()
        self.gap_num_target: dict = {}
        self.selling_orders: list = []  # 当日在卖
        self.before_yesterday_buy: set = set()  # 昨天之前买的

    def init(self, context: SimContext, data: SimDataService):
        # 只对市值超过500亿的做回测
        mv_arr: list = data.get_daily_metrics([self.to_dt], [mq_daily_metric_enum.total_mv.name])
        for mv in mv_arr:  # type: MqDailyMetric
            if mv.value >= 500 * 10000 * 10000:
                self.target.add(mv.ts_code)
                self.gap[mv.ts_code] = []
                self.gap_num_target[mv.ts_code] = self.standard_gap_num

    def morning_auction(self, context: SimContext, data: SimDataService):
        dt: str = context.get_dt()
        shares: list = context.get_holding()
        self.selling_orders = []
        for (ts_code, share) in shares.items():  # type: str, SimShareHold
            p: SimDailyPrice = context.get_today_price(ts_code)
            gap: list = self.gap[ts_code]

            for gap_price in gap:
                gap_price.update_adj('qfq', p.adj)

            if len(gap) < self.gap_num_target[ts_code] - 1:
                # 买入目标缺口数 = 当前缺口数 + 1。已经补了一个缺口，无条件卖出
                self.selling_orders.append(context.sell_share(ts_code, p.down_limit))
            elif ts_code in self.before_yesterday_buy:
                # 第三日无条件卖出
                self.selling_orders.append(context.sell_share(ts_code, p.down_limit))
            else:
                # 按补缺卖出
                min_low = p.up_limit
                for gap_price in self.gap[ts_code]:
                    if gap_price.low < min_low:
                        min_low = gap_price.low
                self.selling_orders.append(context.sell_share(ts_code, min_low))

    def before_trade(self, context: SimContext, data: SimDataService):
        holding: dict = context.get_holding()
        dt: str = context.get_dt()
        to_buy = []
        to_sell = []
        for ts_code in self.target:
            ts_gap: list = self.gap[ts_code]
            p: SimDailyPrice = context.get_today_price(ts_code)

            if ts_code in self.last_trade_price and p.is_trade == 1:
                lp: SimDailyPrice = self.__get_last_trade_day_price(ts_code, p)
                if p.open < lp.low:
                    # 缺口
                    ts_gap.append(lp)
                    log.info('New gap: %s %s %.2f. Gap num: %d' % (ts_code, context.get_dt(), lp.low, len(ts_gap)))

            if len(ts_gap) >= self.gap_num_target[ts_code]:
                if ts_code in holding:
                    # 已经持有了，还在往下跳缺口，垃圾货要赶紧卖了
                    to_sell.append(ts_code)
                else:
                    to_buy.append(ts_code)

        for ts_code in to_sell:  # type: str
            # 取消已有的卖出订单，然后无条件卖出
            for o in self.selling_orders:  # type SimOrder
                if o.get_ts_code() == ts_code:
                    context.retrieve_order(o)

            p: SimDailyPrice = context.get_today_price(ts_code)
            context.sell_share(ts_code, p.down_limit)

        # 尽量等权买入
        for i in range(len(to_buy)):
            max_num = len(to_buy) - i
            ts_code = to_buy[i]
            p: SimDailyPrice = context.get_today_price(ts_code)
            context.buy_amap(ts_code, p.open, context.get_cash() / max_num)

    def after_trade(self, context: SimContext, data: SimDataService):
        # 清除已补的缺口，或30天前的缺口
        dt: str = context.get_dt()
        old_dt: str = date_utils.format_delta(dt, -30)
        for ts_code in self.target:
            p: SimDailyPrice = context.get_today_price(ts_code)
            if p is None or p.is_trade == 0:
                # 未上市 或 停牌就不用看了
                continue
            self.last_trade_price[ts_code] = p
            ts_gap: list = self.gap[ts_code]

            if len(ts_gap) == 0:
                continue

            to_remove: list = []
            for gap_price in ts_gap:  # type: SimDailyPrice
                if gap_price.trade_date < old_dt or p.high >= gap_price.low:
                    to_remove.append(gap_price)

            if len(to_remove) > 0:
                for r in to_remove:  # type: SimDailyPrice
                    ts_gap.remove(r)
                log.info('Gap clear: %s %s %.2f. Gap num: %d' % (ts_code, dt, gap_price.low, len(ts_gap)))

        self.yesterday_buy = set()
        just_buy: dict = context.get_holding_just_buy()
        for ts_code in just_buy:  # type: str
            self.yesterday_buy.add(ts_code)

        self.before_yesterday_buy = set()
        old_holdings: dict = context.get_holding()
        for ts_code in old_holdings:  # type: str
            self.before_yesterday_buy.add(ts_code)

        # 新的缺口数目标应该是 max(剩余缺口数+1，标准缺口数)
        for ts_code in self.target:  # type: str
            new_gap_num: int = len(self.gap[ts_code]) + 1
            if new_gap_num < self.standard_gap_num:
                new_gap_num = self.standard_gap_num
            self.gap_num_target[ts_code] = new_gap_num

    def __get_last_trade_day_price(self, ts_code: str, now_price: SimDailyPrice):
        """
        拿上一个交易日的价格，可能除权了，重新复权
        :param ts_code: 股票编码
        :param now_price: 当前价格
        :return:
        """
        if ts_code not in self.last_trade_price:
            return None
        p: SimDailyPrice = self.last_trade_price[ts_code]
        p.update_adj('qfq', now_price.adj)
        return p


def run(from_dt: str = '20210218', to_dt: str = '20210507', standard_gap_num: int = 3):
    """
    向下缺口买入策略
    :param from_dt: 回测开始日期
    :param to_dt: 回测结束日期
    :param standard_gap_num: 买入的标准缺口数
    :return:
    """
    strategy: DownGapN = DownGapN(from_dt, to_dt, standard_gap_num)
    center: SimCenter = SimCenter(strategy, from_dt, to_dt)
    center.run()


if __name__ == '__main__':
    run()
