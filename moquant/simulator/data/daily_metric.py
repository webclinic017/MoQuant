from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.utils import date_utils


class SimDailyMetricService(object):

    def __init__(self):
        pass

    def get_daily_metrics(self, dates: list, metrics: list, ts_codes: list = None):
        """
        获取日指标
        :param dates: 日期列表 必填
        :param metrics: 指标列表 见 mq_daily_metric_enum，必填
        :param ts_codes: 股票编码列表 不填时获取全部公司
        :return:
        """
        for d in dates:
            if not date_utils.is_valid_dt(d):
                raise Exception('Invalid date %s' % d)
        session: Session = db_client.get_session()
        ml: list = session.query(MqDailyMetric) \
            .filter(MqDailyMetric.ts_code.in_(ts_codes) if ts_codes is not None else 1 == 1,
                    MqDailyMetric.update_date.in_(dates), MqDailyMetric.name.in_(metrics))
        session.close()
        return ml

    def get_daily_metrics_with_period(self, from_date: str, to_date: str, metrics: list, ts_codes: list = None):
        """
        获取日指标
        :param from_date: 开始日期
        :param to_date: 结束日期
        :param metrics: 指标列表 见 mq_daily_metric_enum
        :param ts_codes: 股票编码列表
        :return:
        """
        if not date_utils.is_valid_dt(from_date):
            raise Exception('Invalid date %s' % from_date)
        if not date_utils.is_valid_dt(to_date):
            raise Exception('Invalid date %s' % to_date)

        session: Session = db_client.get_session()
        ml: list = session.query(MqDailyMetric) \
            .filter(MqDailyMetric.ts_code.in_(ts_codes) if ts_codes is not None else 1 == 1,
                    MqDailyMetric.update_date >= from_date, MqDailyMetric.update_date <= to_date,
                    MqDailyMetric.name.in_(metrics))
        session.close()
        return ml
