from moquant.log import get_logger
from moquant.simulator.data.calendar import SimCalendarService
from moquant.simulator.data.dividend import SimDividendService
from moquant.simulator.data.price import SimPriceService

log = get_logger(__name__)


class SimDataService(SimCalendarService, SimDividendService, SimPriceService):

    def __init__(self):
        pass

    def get_daily_metrics(self,
                          ts_codes: dict(type=list, help="股票编码列表"),
                          metrics: dict(type=list, help="指标列表"),
                          dates: dict(type=list, help="日期列表")):
        pass
