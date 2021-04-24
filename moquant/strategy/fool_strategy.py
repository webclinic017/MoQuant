from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.log import get_logger
from moquant.simulator.data import SimDataService
from moquant.simulator.sim_center import SimCenter
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler

log = get_logger(__name__)


class FoolStrategyHandler(SimHandler):

    def init(self, context: SimContext, data: SimDataService):
        pass

    def morning_auction(self, context: SimContext, data: SimDataService):
        dt = context.get_dt()
        price: MqDailyPrice = data.get_qfq_price('000050.SZ', dt, dt)[0]
        context.buy_amap('000050.SZ', price.pre_close_qfq)

    def before_trade(self, context: SimContext, data: SimDataService):
        pass


if __name__ == '__main__':
    strategy: FoolStrategyHandler = FoolStrategyHandler()
    center: SimCenter = SimCenter(strategy, '20200428', '20200527')
    center.run()
