import pandas as pd
from pandas import DataFrame, Series
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.log import get_logger
from moquant.scripts import cal_grow
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler

log = get_logger(__name__)


class GrowStrategyHandler(SimHandler):

    def auction_before_trade(self, context: SimContext):
        session: Session = db_client.get_session()
        dt = context.get_dt()
        grow_df: DataFrame = cal_grow.get_grow_df(dt)
        code_col: Series = grow_df['ts_code'].values
        holding = context.get_holding()

        # sell not in grow list
        for share in holding:  # type: SimShareHold
            if not share.get_ts_code() in code_col:
                context.sell_share(share.get_ts_code(), share.get_num())



    def auction_before_end(self, context: SimContext):
        pass


if __name__ == '__main__':
    s = pd.Series(['ab', 'bc'])
    log.info('ab' in s.values)
