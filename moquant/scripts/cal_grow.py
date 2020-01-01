from decimal import Decimal

from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.log import get_logger

log = get_logger(__name__)


def cal_growing_score(share: MqDailyBasic, quarter: MqQuarterBasic,
                      basic_profit: Decimal = Decimal(1000 * 10000), max_peg: Decimal = Decimal(0.2)):
    score = 0
    if share.dprofit_pe is None or share.dprofit_pe > 50:
        score = -1
    elif share.quarter_dprofit_yoy is None or share.quarter_dprofit_yoy < 0.5:
        score = -1
    elif share.dprofit_peg is None or share.dprofit_peg > max_peg or share.dprofit_peg < 0:
        score = -1

    if score != -1:
        if quarter is None:
            score = -1
        elif quarter.quarter_dprofit_ly is None or abs(quarter.quarter_dprofit_ly) < basic_profit:
            score = -1
        elif quarter.quarter_dprofit is None or quarter.dprofit_ltm is None or \
                abs(quarter.quarter_dprofit / quarter.dprofit_ltm < 0.15):
            score = -1

    if score != -1:
        score = (1 - share.dprofit_peg / max_peg) * 100

    return max(score, 0)
