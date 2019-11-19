import pandas as pd
from pandas import DataFrame, Series
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.log import get_logger
from moquant.scripts import cal_grow
from moquant.simulator.sim_order import SimOrder
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_price import SimSharePrice

log = get_logger(__name__)


class GrowStrategyHandler(SimHandler):

    def auction_before_trade(self, context: SimContext):
        session: Session = db_client.get_session()
        dt = context.get_dt()
        grow_df: DataFrame = cal_grow.get_grow_df(dt)
        code_col: Series = grow_df['ts_code'].values
        holding: dict = context.get_holding()

        for ts_code, share in holding:  # type: str, SimShareHold
            if ts_code not in code_col:
                # sell not in grow list
                context.sell_share(share.get_ts_code(), share.get_num())
            if share.achieve_win() or share.achieve_lose():
                # sell achieve goal
                context.sell_share(share.get_ts_code(), share.get_num())

        for index, stock in grow_df.iterrows():
            max_buy = 50000
            if stock.ts_code in holding:
                hold: SimShareHold = holding[stock.ts_code]
                max_buy = max_buy - hold.get_cost()
                continue
            price: SimSharePrice = context.get_price(stock.ts_code)
            context.buy_amap(stock.ts_code, price.get_up_limit(), max_buy)

    def auction_before_end(self, context: SimContext):
        pass


if __name__ == '__main__':
    s = pd.Series(['ab', 'bc'])
    log.info('ab' in s.values)
