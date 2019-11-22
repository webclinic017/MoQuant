from pandas import DataFrame
from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils.datetime import format_delta

log = get_logger(__name__)


class SimDataService(object):
    __st: str
    __ed: str
    __cache: bool

    # trade cal
    __sz: set
    __sh: set

    __daily_info: dict
    __stk_limit: dict
    __dividend: dict

    def __init__(self, st, ed, cache: bool = False):
        self.__st = st
        self.__ed = ed
        self.__cache = cache

        if cache:
            session: Session = db_client.get_session()
            self.__init_trade_cal(st, ed)
            self.__init_daily_info(st, ed, session)
            self.__init_stk_limit(st, ed, session)
            self.__init_dividend(st, ed, session)

    def __get_trade_cal_sz(self, st, ed) -> set:
        sz: DataFrame = ts_client.fetch_trade_cal(exchange='SZSE', start_date=st, end_date=ed, is_open=1)
        return set([s.cal_date for i, s in sz.iterrows()])

    def __get_trade_cal_sh(self, st, ed) -> set:
        sh: DataFrame = ts_client.fetch_trade_cal(exchange='SSE', start_date=st, end_date=ed, is_open=1)
        return set([s.cal_date for i, s in sh.iterrows()])

    def __init_trade_cal(self, st, ed):
        self.__sz = self.__get_trade_cal_sz(st, ed)
        self.__sh = self.__get_trade_cal_sh(st, ed)
        log.info('Init trade cal')

    def __init_daily_info(self, st, ed, session: Session):
        self.__daily_info = {}
        x = st
        while x <= ed:
            y = format_delta(x, 100)
            if y > ed:
                y = ed
            daily_info_list = session.query(TsDailyTradeInfo).filter(
                and_(TsDailyTradeInfo.trade_date >= x, TsDailyTradeInfo.trade_date <= y)).all()
            for daily in daily_info_list:  # type: TsDailyTradeInfo
                date = daily.trade_date
                if date not in self.__daily_info:
                    self.__daily_info[date] = []
                self.__daily_info[date].append(daily)
            x = format_delta(y, 1)
        log.info('Init daily info')

    def __init_stk_limit(self, st, ed, session: Session):
        self.__stk_limit = {}
        x = st
        while x <= ed:
            y = format_delta(x, 100)
            if y > ed:
                y = ed
            limit_list = session.query(TsStkLimit).filter(
                and_(TsStkLimit.trade_date >= x, TsStkLimit.trade_date <= y)).all()
            for limit in limit_list:  # type: TsStkLimit
                date = limit.trade_date
                if date not in self.__stk_limit:
                    self.__stk_limit[date] = []
                self.__stk_limit[date].append(limit)
            x = format_delta(y, 1)
        log.info('Init stk limit')

    def __init_dividend(self, st, ed, session: Session):
        self.__dividend = {}
        x = st
        while x <= ed:
            y = format_delta(x, 100)
            if y > ed:
                y = ed
            dividend_list = session.query(TsDividend).filter(
                and_(TsDividend.div_proc == '实施', TsDividend.record_date >= x, TsDividend.record_date <= y)).all()
            for dividend in dividend_list:  # type: TsDividend
                date = dividend.record_date
                if date not in self.__dividend:
                    self.__dividend[date] = []
                self.__dividend[date].append(dividend)
            x = format_delta(y, 1)
        log.info('Init dividend')

    def get_sz_trade_cal(self) -> set:
        return self.__sz if self.__cache else self.__get_trade_cal_sz(self.__st, self.__ed)

    def get_sh_trade_cal(self) -> set:
        return self.__sh if self.__cache else self.__get_trade_cal_sh(self.__st, self.__ed)

    def __get_daily_info_from_db(self, dt: str) -> list:
        session: Session = db_client.get_session()
        return session.query(TsDailyTradeInfo).filter(TsDailyTradeInfo.trade_date == dt).all()

    def get_daily_info(self, dt: str) -> list:
        if self.__cache:
            if dt in self.__daily_info:
                return self.__daily_info[dt]
            else:
                log.error('Daily info not init %s' % dt)
        return self.__get_daily_info_from_db(dt)

    def __get_stk_limit_from_db(self, dt: str) -> list:
        session: Session = db_client.get_session()
        return session.query(TsStkLimit).filter(TsStkLimit.trade_date == dt).all()

    def get_stk_limit(self, dt: str) -> list:
        if self.__cache:
            if dt in self.__stk_limit:
                return self.__stk_limit[dt]
            else:
                log.error('Stk limit not init %s' % dt)
        return self.__get_stk_limit_from_db(dt)

    def __get_dividend_from_db(self, dt):
        session: Session = db_client.get_session()
        return session.query(TsDividend).filter(and_(TsDividend.div_proc == '实施', TsDividend.record_date == dt)).all()

    def get_dividend(self, dt: str) -> list:
        if self.__cache:
            if dt in self.__dividend:
                return self.__dividend[dt]
            else:
                log.error('Dividend not init %s' % dt)
        return self.__get_dividend_from_db(dt)
