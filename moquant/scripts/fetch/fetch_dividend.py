import time

from pandas import DataFrame
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_dividend import TsDividend
from moquant.log import get_logger
from moquant.scripts.fetch import clear_after_fetch
from moquant.tsclient import ts_client
from moquant.utils import date_utils

log = get_logger(__name__)


def common_fetch_dividend(ts_code: str = None, dt: str = None):
    target: str = dt if ts_code is None else ts_code
    df: DataFrame = None
    for cnt in range(2):
        log.info('To fetch dividend %s' % target)
        try:
            # https://tushare.pro/document/2?doc_id=103 分红
            df = ts_client.fetch_dividend(ts_code=ts_code, imp_ann_date=dt)
            break
        except Exception as e:
            log.error('Calling TuShare too fast. Will sleep 1 minutes...')
            time.sleep(60)
            ts_client.init_token()

    if df is not None and not df.empty:
        db_client.store_dataframe(df, TsDividend.__tablename__)
        log.info('Successfully save dividend %s' % target)
        fix_dividend(ts_code, df['imp_ann_date'].min(), df['imp_ann_date'].max())


def fetch_dividend_by_date(dt: str):
    common_fetch_dividend(ts_code=None, dt=dt)


def update_dividend_to(dt: str):
    session: Session = db_client.get_session()
    td: list = session.query(TsDividend).order_by(TsDividend.imp_ann_date.desc()).limit(1).all()
    session.close()

    now: str = fetch_data_start_date if len(td) == 0 else date_utils.format_delta(td[0].imp_ann_date, 1)

    while now <= dt:
        fetch_dividend_by_date(now)
        now = date_utils.format_delta(now, 1)


def init_dividend():
    """
    按股票初始化分红数据
    :return:
    """
    session: Session = db_client.get_session()
    basic_list = session.query(TsBasic).all()
    session.close()
    for basic in basic_list:  # type: TsBasic
        session: Session = db_client.get_session()
        td: list = session.query(TsDividend).filter(TsDividend.ts_code == basic.ts_code).limit(1).all()
        session.close()
        if len(td) == 0:
            common_fetch_dividend(basic.ts_code)
        db_client.execute_sql(clear_after_fetch.clear_duplicate_dividend(basic.ts_code))
        db_client.execute_sql(clear_after_fetch.clear_duplicate_dividend_2(basic.ts_code))
        log.info('clear duplicate %s' % basic.ts_code)


# 个人发现的有问题的分红数据，或者已确认的特殊分红，以东财数据为准
to_fix_list = [
    {'ts_code': '000001.SZ', 'end_date': '20070615', 'imp_ann_date': '20070614', 'div_proc': '实施',
     'ex_date': '20070618', 'pay_date': '20070618'},
    {'ts_code': '000031.SZ', 'end_date': '20060210', 'imp_ann_date': '20060209', 'div_proc': '实施',
     'cash_div': 0.17 * 0.9, 'cash_div_tax': 0.17, 'ex_date': '20060214', 'pay_date': '20060214'},
    {'ts_code': '000680.SZ', 'end_date': '20060526', 'imp_ann_date': '20060525', 'div_proc': '实施'},
    {'ts_code': '000776.SZ', 'end_date': '20100302', 'imp_ann_date': '20100428', 'div_proc': '实施'},
    {'ts_code': '000883.SZ', 'end_date': '20101031', 'imp_ann_date': '20110118', 'div_proc': '实施'},
    {'ts_code': '000975.SZ', 'end_date': '20080123', 'imp_ann_date': '20080118', 'div_proc': '实施'},
    {'ts_code': '000900.SZ', 'end_date': '20060626', 'imp_ann_date': '20060623', 'div_proc': '实施'},
    {'ts_code': '000989.SZ', 'end_date': '20060518', 'imp_ann_date': '20060517', 'div_proc': '实施',
     'cash_div': 0.224 * 0.8, 'cash_div_tax': 0.224},
    {'ts_code': '000531.SZ', 'end_date': '20060216', 'imp_ann_date': '20060214', 'div_proc': '实施',
     'cash_div': 0.927 * 0.9, 'cash_div_tax': 0.927, 'ex_date': '20060220', 'pay_date': '20060220'},
    {'ts_code': '002142.SZ', 'end_date': '20171109', 'imp_ann_date': '20171109', 'div_proc': '实施',
     'cash_div': 0, 'cash_div_tax': 0},
    {'ts_code': '000912.SZ', 'end_date': '20060209', 'imp_ann_date': '20060208', 'div_proc': '实施',
     'cash_div': 0.512 * 0.9, 'cash_div_tax': 0.512},
    {'ts_code': '002041.SZ', 'end_date': '20051123', 'imp_ann_date': '20051123', 'div_proc': '实施'},
    {'ts_code': '000623.SZ', 'end_date': '20050801', 'imp_ann_date': '20050801', 'div_proc': '实施',
     'ex_date': '20050802', 'pay_date': '20050802'},
    {'ts_code': '601336.SH', 'end_date': '20120111', 'imp_ann_date': '20120810', 'div_proc': '实施'},
    {'ts_code': '002202.SZ', 'end_date': '20100729', 'imp_ann_date': '20100723', 'div_proc': '实施'},
    {'ts_code': '600035.SH', 'end_date': '20061222', 'imp_ann_date': '20061221', 'div_proc': '实施'},
]


def fix_dividend(ts_code: str = None, from_date: str = None, to_date: str = None):
    """
    清理一些脏数据
    :param ts_code:
    :param from_date:
    :param to_date:
    :return:
    """

    for i in to_fix_list:
        if ts_code is not None and ts_code != i['ts_code']:
            continue
        if from_date is not None and to_date is not None \
                and from_date <= i['imp_ann_date'] <= to_date:
            session: Session = db_client.get_session()
            d: TsDividend = session.query(TsDividend) \
                .filter(TsDividend.ts_code == i['ts_code'], TsDividend.end_date == i['end_date'],
                        TsDividend.imp_ann_date == i['imp_ann_date'], TsDividend.div_proc == i['div_proc']).one()
            for key in i:
                setattr(d, key, i[key])
            d.is_fix = 1
            session.flush([d])
            session.close()


if __name__ == '__main__':
    init_dividend()
