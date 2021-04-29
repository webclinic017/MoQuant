from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.log import get_logger

log = get_logger(__name__)


class SimPriceService(object):

    def __init__(self):
        pass

    def get_qfq_price_in(self, ts_code_arr: list, now_date: str, date_arr: list):
        """
        获取股票的每日价格信息 - 前复权
        :param ts_code_arr: 股票编码列表
        :param now_date: 查看数据的日期，会显示当时能看到的前复权价格
        :param date_arr: 获取价格的时间
        :return: list(MqDailyPrice)
        """
        if ts_code_arr is None or len(ts_code_arr) == 0:
            date_where = '1=1'
        else:
            date_where = "a.trade_date in ('" + "','".join(date_arr) + "')"
        return self.__common_query(self.__get_code_where(ts_code_arr), now_date, date_where)

    def get_qfq_price(self, ts_code_arr: list, now_date: str, from_date: str, to_date: str) -> list:
        """
        获取股票的每日价格信息 - 前复权
        :param ts_code_arr: 股票编码列表
        :param now_date: 查看数据的日期，会显示当时能看到的前复权价格
        :param from_date: 获取价格的时间段 开始时间
        :param to_date: 获取价格的时间段 结束时间
        :return: list(MqDailyPrice)
        """
        date_where: str = "a.trade_date >= '%s' and a.trade_date <= '%s'" % (from_date, to_date)
        return self.__common_query(self.__get_code_where(ts_code_arr), now_date, date_where)

    def __get_code_where(self, ts_code_arr: list):
        """
        将股票编码列表转化成sql的where
        :param ts_code_arr:
        :return:
        """
        if ts_code_arr is None or len(ts_code_arr) == 0:
            code_where = '1=1'
        else:
            code_where = 'a.ts_code in (\'' + '\',\''.join(ts_code_arr) + '\')'
        return code_where

    def __common_query(self, code_where: str, now_date: str, date_where: str):
        """
        封装好的底层查询，按需放入where即可
        :param code_where: 股票筛选条件
        :param now_date: 查看数据的日期
        :param date_where: 查询日期的条件
        :return:
        """
        sql = """
            select
                a.* 
            from mq_daily_price a
            left join 
            (
                select
                ts_code, max(div_date) as div_date
                from mq_daily_price a
                where %s and div_date <= '%s'
                group by ts_code
            ) b
            on a.ts_code = b.ts_code and a.div_date = b.div_date
            where a.div_date <= '%s'
            and %s and %s
            """ % (code_where, now_date, now_date, date_where, code_where)
        return db_client.query_with_sql(sql, MqDailyPrice)
