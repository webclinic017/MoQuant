from moquant.log import get_logger

log = get_logger(__name__)


class SimPriceService(object):

    def __init__(self):
        pass

    def get_qfq_price(self, ts_code_arr: list, now_date: str,
                      from_date: str, to_date: str) -> list:
        """
        获取股票的每日价格信息 - 前复权
        :param ts_code_arr: 股票编码列表
        :param now_date: 查看数据的日期，会显示当时能看到的前复权价格
        :param from_date: 获取价格的时间段 开始时间
        :param to_date: 获取价格的时间段 结束时间
        :return: MqDailyPrice
        """
        pass
