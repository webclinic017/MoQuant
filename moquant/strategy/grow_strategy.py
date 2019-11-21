from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_share_price import SimSharePrice
from moquant.utils.datetime import format_delta

log = get_logger(__name__)


class GrowStrategyHandler(SimHandler):

    def auction_before_trade(self, context: SimContext):
        session: Session = db_client.get_session()
        dt = context.get_dt()
        data_dt = format_delta(dt, -1)
        grow_list: list = session.query(MqDailyBasic).filter(
            and_(MqDailyBasic.date == data_dt, MqDailyBasic.grow_score != -1)) \
            .order_by(MqDailyBasic.grow_score.desc()).all()
        code_col: list = [i.ts_code for i in grow_list]
        holding: dict = context.get_holding()

        for ts_code in holding:  # type: str
            share: SimShareHold = holding[ts_code]
            if share.get_can_sell() == 0:
                continue
            if ts_code not in code_col:
                # sell not in grow list
                context.sell_share(share.get_ts_code(), share.get_num())
            elif share.achieve_win() or share.achieve_lose():
                # sell achieve goal
                context.sell_share(share.get_ts_code(), share.get_num())

        for stock in grow_list:  # type: MqDailyBasic
            max_buy = 50000
            if stock.ts_code in holding:
                hold: SimShareHold = holding[stock.ts_code]
                max_buy = max_buy - hold.get_cost()
                continue
            cash = context.get_cash()
            price: SimSharePrice = context.get_price(stock.ts_code)
            if price is not None and cash >= price.get_up_limit() * 100:
                context.buy_amap(stock.ts_code, price.get_up_limit(), max_buy)

    def auction_before_end(self, context: SimContext):
        pass
