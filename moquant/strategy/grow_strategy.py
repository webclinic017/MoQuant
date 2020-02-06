from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.log import get_logger
from moquant.simulator.sim_context import SimContext
from moquant.simulator.sim_handler import SimHandler
from moquant.simulator.sim_share_hold import SimShareHold
from moquant.simulator.sim_share_price import SimSharePrice
from moquant.utils.date_utils import format_delta

log = get_logger(__name__)


class GrowStrategyHandler(SimHandler):
    __ban: dict
    __quarter: dict

    def __init__(self):
        self.__ban = {}
        self.__quarter = {}

    def init(self, context: SimContext):
        st, ed = context.get_simulate_period()
        from_date = format_delta(st, -90)
        session: Session = db_client.get_session()
        quarter_list: list = session.query(MqQuarterBasic)\
            .filter(MqQuarterBasic.update_date >= from_date, MqQuarterBasic.adjust_ly == '0')\
            .order_by(MqQuarterBasic.update_date.asc(), MqQuarterBasic.report_period.asc()).all()
        session.close()
        for quarter in quarter_list: # type: MqQuarterBasic
            if quarter.ts_code not in self.__quarter:
                self.__quarter[quarter.ts_code] = quarter

    def auction_before_trade(self, context: SimContext):
        session: Session = db_client.get_session()
        dt = context.get_dt()
        data_dt = format_delta(dt, -1)
        grow_list: list = session.query(MqDailyBasic)\
            .filter(MqDailyBasic.date == data_dt, MqDailyBasic.grow_score != -1, MqQuarterBasic.adjust_ly == '0') \
            .order_by(MqDailyBasic.grow_score.desc()).all()
        quarter_list: list = session.query(MqQuarterBasic).filter(MqQuarterBasic.update_date == data_dt).all()
        session.close()
        for quarter in quarter_list: # type: MqQuarterBasic
            if quarter.ts_code not in self.__quarter:
                self.__quarter[quarter.ts_code] = quarter

        to_buy = set()
        period_map: dict = {}
        for daily in grow_list:  # type: MqDailyBasic
            to_buy.add(daily.ts_code)
            period_map[daily.ts_code] = daily.dprofit_period

        to_sell = set()
        for ts_code in self.__quarter:
            quarter: MqQuarterBasic = self.__quarter[ts_code]
            if quarter.receive_risk is not None and quarter.receive_risk > 0.5:
                to_sell.add(ts_code)
            if quarter.liquidity_risk is not None and quarter.liquidity_risk > 0.6:
                to_sell.add(ts_code)
            if quarter.intangible_risk is not None and quarter.intangible_risk > 0.25:
                to_sell.add(ts_code)

        holding: dict = context.get_holding()

        for ts_code in holding:  # type: str
            share: SimShareHold = holding[ts_code]
            if share.get_can_sell() == 0:
                continue
            if ts_code not in to_buy or ts_code in to_sell:
                # sell not in grow list
                context.sell_share(share.get_ts_code(), share.get_num())
            elif share.achieve_win() or share.achieve_lose():
                # sell achieve goal
                context.sell_share(share.get_ts_code(), share.get_num())
                self.__add_to_ban(period_map, ts_code)

        for stock in grow_list:  # type: MqDailyBasic
            if self.__is_ban(stock):
                continue
            if stock.ts_code in holding:
                continue
            if stock.ts_code in to_sell:
                continue
            max_buy = 55000
            cash = context.get_cash()
            if cash <= max_buy:
                continue
            price: SimSharePrice = context.get_price(stock.ts_code)
            if price is not None and cash >= price.get_up_limit() * 100:
                context.buy_amap(stock.ts_code, price.get_up_limit(), max_buy)

    def auction_before_end(self, context: SimContext):
        pass

    def __is_ban(self, daily: MqDailyBasic):
        return daily.ts_code in self.__ban and daily.dprofit_period == self.__ban[daily.ts_code]

    def __add_to_ban(self, period_map: dict, ts_code: str):
        if ts_code not in period_map:
            return
        self.__ban[ts_code] = period_map[ts_code]
        log.info("Not to buy %s in %s" % (ts_code, period_map[ts_code]))

    def __remove_ban(self, period_map: dict):
        to_remove = set()
        for ts_code in self.__ban:
            if ts_code not in period_map or self.__ban[ts_code] != period_map[ts_code]:
                to_remove.add(ts_code)
        for ts_code in to_remove:
            self.__ban.pop(ts_code)
