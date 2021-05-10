from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_center import SimCenter
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_daily_price import SimDailyPrice
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_hold import SimShareHold

log = get_logger(__name__)


class NormalBuy(SimHandler):

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        dt = context.get_dt()
        price: SimDailyPrice = data.get_qfq_price(['000050.SZ'], dt, dt, dt)[0]
        context.buy_amap('000050.SZ', price.pre_close)

        if dt == '20200527':
            s: SimShareHold = context.get_hold('000050.SZ')
            context.sell_share(s.get_ts_code(), price.pre_close)

    def before_trade(self, context: SimContext, data: SimDataService):
        pass


if __name__ == '__main__':
    strategy: NormalBuy = NormalBuy()
    center: SimCenter = SimCenter(strategy, '20200428', '20200528')
    center.run()
