#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To init table, will not create if table exists """

import moquant.dbclient as client
from moquant.dbclient.base import Base
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.dbclient.mq_dcf_config import MqDcfConfig
from moquant.dbclient.mq_manual_metric import MqManualMetric
from moquant.dbclient.mq_message import MqMessage
from moquant.dbclient.mq_quarter_metric import MqQuarterMetric
from moquant.dbclient.mq_sys_param import MqSysParam
from moquant.dbclient.ts_adj_factor import TsAdjFactor
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_dividend import TsDividend
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.dbclient.ts_trade_cal import TsTradeCal


def create_table():
    engine = client.db_client.get_engine()
    all_table = [MqSysParam, MqManualMetric, MqDcfConfig,
                 MqQuarterMetric, MqDailyMetric, MqMessage,
                 TsBasic, TsDailyBasic, TsDailyTradeInfo, TsAdjFactor,
                 TsIncome, TsBalanceSheet, TsCashFlow, TsForecast, TsExpress,
                 TsFinaIndicator, TsDividend, TsStkLimit, TsTradeCal]

    Base.metadata.create_all(engine)
