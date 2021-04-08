man_forecast = 0
forecast = 1
forecast_fix = 2
express = 3
express_fix = 4
report = 5
report_fix = 6
report_adjust = 7
report_adjust_fix = 8
mq_predict = 9

none_report_type = 99


def is_report(t: int) -> bool:
    """
    返回是否季度报
    """
    return t == report or t == report_adjust
