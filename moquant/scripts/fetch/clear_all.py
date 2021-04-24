from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.dbclient.mq_daily_price import MqDailyPrice
from moquant.dbclient.mq_quarter_metric import MqQuarterMetric
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.utils import env_utils


def run():
    args = env_utils.get_args()
    ts_code = args.code
    session: Session = db_client.get_session()

    session.query(TsStkLimit).filter(TsStkLimit.ts_code == ts_code).delete()
    session.query(TsDailyBasic).filter(TsDailyBasic.ts_code == ts_code).delete()
    session.query(TsIncome).filter(TsIncome.ts_code == ts_code).delete()
    session.query(TsBalanceSheet).filter(TsBalanceSheet.ts_code == ts_code).delete()
    session.query(TsCashFlow).filter(TsCashFlow.ts_code == ts_code).delete()
    session.query(TsDividend).filter(TsDividend.ts_code == ts_code).delete()
    session.query(TsForecast).filter(TsForecast.ts_code == ts_code).delete()
    session.query(TsExpress).filter(TsExpress.ts_code == ts_code).delete()
    session.query(TsFinaIndicator).filter(TsFinaIndicator.ts_code == ts_code).delete()
    session.query(MqDailyMetric).filter(MqDailyMetric.ts_code == ts_code).delete()
    session.query(MqQuarterMetric).filter(MqQuarterMetric.ts_code == ts_code).delete()
    session.query(MqDailyPrice).filter(MqDailyPrice.ts_code == ts_code).delete()

