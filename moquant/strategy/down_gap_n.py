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

    def __init__(self, gap_num: int):
        self.target: set = set()
        self.gap: dict = {}
        self.last_trade_date: dict = {}  # 上一个交易日
        self.yesterday_buy: set = set()
        self.gap_num: int = gap_num

    def init(self, context: SimContext, data: SimDataService):
        # 只对市值超过500亿的做回测
        mv_arr: list = data.get_daily_metrics(['20210428'], [mq_daily_metric_enum.total_mv.name])
        for mv in mv_arr:  # type: MqDailyMetric
            if mv.value >= 500 * 10000 * 10000:
                self.target.add(mv.ts_code)
                self.gap[mv.ts_code] = set()
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        dt: str = context.get_dt()
        shares: list = context.get_holding()
        for i in shares:  # type: SimShareHold
            ts_code: str = i.get_ts_code()
            p: SimDailyPrice = context.get_today_price(ts_code)
            gap: set = self.gap[ts_code]
            if ts_code in self.yesterday_buy:
                # 第三日无条件卖出
                context.sell_share(ts_code, i.get_num(), p.down_limit)
            elif len(gap) < 3:
                # 已经补了一个缺口，无条件卖出
                context.sell_share(ts_code, i.get_num(), p.down_limit)
            else:
                # 按补缺卖出
                lp: SimDailyPrice = self.__get_last_trade_day_price(data, ts_code, dt, self.last_trade_date[ts_code])
                context.sell_share(ts_code, i.get_num(), lp.low)

    def before_trade(self, context: SimContext, data: SimDataService):
        dt: str = context.get_dt()
        to_buy = []
        for ts_code in self.target:
            ts_gap: set = self.gap[ts_code]
            p: SimDailyPrice = context.get_today_price(ts_code)

            if ts_code in self.last_trade_date and p.is_trade == 1:
                lp: SimDailyPrice = self.__get_last_trade_day_price(data, ts_code, dt, self.last_trade_date[ts_code])
                if p.open < lp.low:
                    # 缺口
                    ts_gap.add(p.trade_date)
                    log.info('New gap: %s %s %.2f. Gap num: %d' % (ts_code, context.get_dt(), lp.low, len(ts_gap)))
            if len(ts_gap) >= self.gap_num:
                to_buy.append(ts_code)

        # 尽量等权买入
        for i in range(len(to_buy)):
            max_num = len(to_buy) - i
            ts_code = to_buy[i]
            p: SimDailyPrice = context.get_today_price(ts_code)
            context.buy_amap(ts_code, p.open, context.get_cash() / max_num)

    def after_trade(self, context: SimContext, data: SimDataService):
        self.yesterday_buy = set()
        just_buy: list = context.get_holding_just_buy()
        for i in just_buy:  # type: SimShareHold
            self.yesterday_buy.add(i.get_ts_code())

        # 清除已补的缺口，或30天前的缺口
        dt: str = context.get_dt()
        old_dt: str = date_utils.format_delta(dt, -30)
        for ts_code in self.target:
            p: SimDailyPrice = context.get_today_price(ts_code)
            if p is None or p.is_trade == 0:
                # 未上市 或 停牌就不用看了
                continue
            self.last_trade_date[ts_code] = dt
            ts_gap: set = self.gap[ts_code]

            if len(ts_gap) == 0:
                continue

            gap_prices: list = data.get_price_in([ts_code], dt, list(ts_gap), 'qfq')
            for gap_price in gap_prices:  # type: SimDailyPrice
                if gap_price.trade_date < old_dt or p.high >= gap_price.low:
                    log.info('Gap clear: %s %s %.2f. Gap num: %d' % (ts_code, dt, gap_price.low, len(ts_gap)))
                    ts_gap.remove(p.trade_date)

    def __get_last_trade_day_price(self, data: SimDataService, ts_code: str, now_date: str, trade_date: str):
        """
        拿上一个交易日的价格，可能除权了
        :param data 获取数据服务
        :param ts_code: 股票编码
        :param now_date: 目前日期
        :param trade_date: 交易日期
        :return:
        """
        if ts_code not in self.last_trade_date:
            return None
        ltd: str = self.last_trade_date[ts_code]
        result: list = data.get_price_in([ts_code], now_date, [trade_date], 'qfq')
        return result[0] if len(result) > 0 else None


if __name__ == '__main__':
    strategy: DownGapN = DownGapN(2)
    center: SimCenter = SimCenter(strategy, '20210218', '20210428')
    center.run()
