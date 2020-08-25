from decimal import Decimal

from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_dcf_config import MqDcfConfig
from moquant.utils import decimal_utils


class MqDcfService(object):
    '''
        根据自由现金流估算市值，分别计算10年，永续
    '''

    def __init__(self, ts_code: str):
        session: Session = db_client.get_session()
        self.arr = session.query(MqDcfConfig).filter(MqDcfConfig.ts_code == ts_code)\
            .order_by(MqDcfConfig.update_date.asc()).all()
        self.global_arr = session.query(MqDcfConfig).filter(MqDcfConfig.ts_code == 'all')\
            .order_by(MqDcfConfig.update_date.asc()).all()
        session.close()

    def cal_dcf(self, fcf: Decimal, year: int, date: str) -> Decimal:
        fcf = decimal_utils.none_to_zero(fcf)
        if fcf <= 0:
            return Decimal(0), Decimal(0)

        inc_map: list = self._get_arr_by_name('inc_rate', date)
        dr_map: list = self._get_arr_by_name('discount_rate', date)

        mv = fcf
        inc_rate = 0.07
        discount_rate = 0.1

        # 计算10年的
        for i in range(0, 10):
            y = year + i + 1
            if y in inc_map:
                inc_rate = inc_map[y].value
            if y in dr_map:
                discount_rate = dr_map[y].value
            fcf = decimal_utils.div(decimal_utils.mul(fcf, (1 + inc_rate)), (1 + discount_rate))
            if fcf < 0:
                fcf = 0
            mv = decimal_utils.add(mv, fcf)

        inc_rate = inc_map[9999].value
        discount_rate = dr_map[9999].value

        mv_forever = decimal_utils.add(mv, decimal_utils.div(
            decimal_utils.mul(fcf, (1 + inc_rate)),
            (discount_rate - inc_rate)))

        return mv, mv_forever

    def _get_arr_by_name(self, name: str, date: str) -> dict:
        year_map = {}
        for cfg in self.global_arr:  # type: MqDcfConfig
            if cfg.update_date > date:
                break
            if cfg.name != name:
                continue
            if cfg.to_year == '9999':
                year_map[cfg.from_year] = cfg
            else:
                for year in range(cfg.from_year, cfg.to_year + 1):
                    year_map[year] = cfg

        for cfg in self.arr:  # type: MqDcfConfig
            if cfg.update_date > date:
                break
            if cfg.name != name:
                continue
            if cfg.to_year == '9999':
                year_map[cfg.from_year] = cfg
            else:
                for year in range(cfg.from_year, cfg.to_year + 1):
                    year_map[year] = cfg

        return year_map
