from moquant.log import get_logger
from moquant.simulator.data.calendar import SimCalendarService
from moquant.simulator.data.daily_metric import SimDailyMetricService
from moquant.simulator.data.dividend import SimDividendService
from moquant.simulator.data.price import SimPriceService

log = get_logger(__name__)


class SimDataService(SimCalendarService, SimDividendService, SimPriceService, SimDailyMetricService):

    def __init__(self):
        super(SimCalendarService, self).__init__()
        super(SimDividendService, self).__init__()
        super(SimPriceService, self).__init__()
        super(SimDailyMetricService, self).__init__()

    def init_cache(self, ts_code_set: set, from_date: str, to_date: str):
        """
        预先缓存指定日期的数据
        :param ts_code_set: 编码列表
        :param from_date: 开始日期
        :param to_date: 结束日期
        :return:
        """
        SimDividendService.init_cache(self, ts_code_set, from_date, to_date)
        SimPriceService.init_cache(self, ts_code_set, from_date, to_date)
