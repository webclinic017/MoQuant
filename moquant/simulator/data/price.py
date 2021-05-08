from sqlalchemy import or_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.log import get_logger
from moquant.simulator import sim_daily_price
from moquant.utils import date_utils

log = get_logger(__name__)


class SimPriceService(object):

    def __init__(self):
        pass

    def get_price_in(self, ts_code_arr: list, now_date: str, date_arr: list, adj_type: str):
        """
        获取股票的每日价格信息
        :param ts_code_arr: 股票编码列表，为空时全取
        :param now_date: 查看数据的日期，会显示当时能看到的前复权价格，需为交易日，不能为空
        :param date_arr: 获取价格的时间，不能为空，必须小于等于 now_date
        :param adj_type: qfq - 前复权, hfq - 后复权, 其他 - 不复权
        :return: list(MqDailyPrice)
        """
        if now_date is None or not date_utils.is_valid_dt(now_date):
            raise Exception('now_date is empty or invalid')
        if date_arr is None or len(date_arr) == 0:
            raise Exception('date_arr cant be empty')
        for d in date_arr:
            if d > now_date:
                raise Exception('Cant get future price %s in %s' % (d, now_date))

        s: Session = db_client.get_session()
        mq_list: list = s.query(MqDailyPrice) \
            .filter(self.__get_code_filter(ts_code_arr),
                    or_(MqDailyPrice.trade_date.in_(date_arr), MqDailyPrice.trade_date == now_date)) \
            .all()
        s.close()

        return self.__convert_to_sim_price(mq_list, adj_type, now_date, now_date not in date_arr)

    def get_price_between(self, ts_code_arr: list, now_date: str, from_date: str, to_date: str, adj_type: str) -> list:
        """
        获取股票的每日价格信息
        :param ts_code_arr: 股票编码列表，为空时全取
        :param now_date: 查看数据的日期，会显示当时能看到的前复权价格，需为交易日，不能为空
        :param from_date: 获取价格的时间段 开始时间，不能为空 必须小于等于 now_date
        :param to_date: 获取价格的时间段 结束时间，不能为空 必须小于等于 now_date
        :param adj_type: qfq - 前复权, hfq - 后复权, 其他 - 不复权
        :return: list(MqDailyPrice)
        """
        if now_date is None or not date_utils.is_valid_dt(now_date):
            raise Exception('now_date is empty or invalid')
        if from_date is None or not date_utils.is_valid_dt(from_date):
            raise Exception('from_date is empty or invalid')
        if to_date is None or not date_utils.is_valid_dt(to_date):
            raise Exception('to_date is empty or invalid')
        if from_date > now_date or to_date > now_date:
            raise Exception('Cant get future price %s~%s in %s' % (from_date, to_date, now_date))

        s: Session = db_client.get_session()
        mq_list: list = s.query(MqDailyPrice) \
            .filter(self.__get_code_filter(ts_code_arr),
                    or_(MqDailyPrice.trade_date.between(from_date, to_date), MqDailyPrice.trade_date == now_date)) \
            .all()
        s.close()

        return self.__convert_to_sim_price(mq_list, adj_type, now_date, now_date > to_date)

    def __get_code_filter(self, ts_code_arr: list):
        return MqDailyPrice.ts_code.in_(ts_code_arr) if ts_code_arr is not None and len(ts_code_arr) > 0 else True

    def __convert_to_sim_price(self, mq_list: list, adj_type: str, now_date: str, remove_now_date: bool) -> list:
        """
        将 MqDailyPrice 转化成 SimDailyPrice，根据 adj_type 进行复权计算
        :param mq_list: MqDailyPrice的数组
        :param adj_type: qfq - 前复权, hfq - 后复权, 其他 - 不复权
        :param now_date: 观察日期
        :param remove_now_date: 是否去除观察日期
        :return: SimDailyPrice的数组
        """
        ret: list = []
        if adj_type == 'qfq':
            max_date_map: dict = {}
            for mq in mq_list:  # type: MqDailyPrice
                if mq.ts_code not in max_date_map or max_date_map[mq.ts_code].trade_date < mq.trade_date:
                    max_date_map[mq.ts_code] = mq

            for mq in mq_list:
                if remove_now_date and mq.trade_date == now_date:
                    continue
                latest: MqDailyPrice = max_date_map[mq.ts_code]
                ret.append(sim_daily_price.from_mq_daily_price(mq, adj_type, latest.adj))
        else:
            for mq in mq_list:
                if remove_now_date and mq.trade_date == now_date:
                    continue
                ret.append(sim_daily_price.from_mq_daily_price(mq, adj_type, 0))

        return ret
