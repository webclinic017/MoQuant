from moquant.log import get_logger
from moquant.simulator.data.calendar import SimCalendarService
from moquant.simulator.data.daily_metric import SimDailyMetricService
from moquant.simulator.data.dividend import SimDividendService
from moquant.simulator.data.price import SimPriceService

log = get_logger(__name__)


class SimDataService(SimCalendarService, SimDividendService, SimPriceService, SimDailyMetricService):

    def __init__(self):
        pass
