import datetime


def format_date(date: datetime, d_format: str = '%Y%m%d') -> str:
    return datetime.datetime.strftime(date, d_format)


def format_delta(d_str: str, day_num: int = 0, d_format: str = '%Y%m%d') -> str:
    d: datetime = parse_str(d_str, d_format)
    return format_date(d + datetime.timedelta(days=day_num))


def get_current_dt() -> str:
    nowd = datetime.datetime.now()
    dt = format_date(nowd + datetime.timedelta(hours=-15)) if nowd.isoweekday() < 6 else format_date(nowd)
    return dt


def parse_str(d_str: str, d_format: str = '%Y%m%d') -> datetime:
    return datetime.datetime.strptime(d_str, d_format)


def date_max(d_arr: list) -> str:
    ans = None
    for d_str in d_arr:
        if d_str is None:
            continue
        if ans is None or d_str > ans:
            ans = d_str
    return ans


def get_quarter_num(d_str: str) -> int:
    return (int(d_str[4:6]) - 1) // 3 + 1 if d_str is not None else None


def get_period(year: int, month: int) -> str:
    day = 30 if month == 6 or month == 9 else 31
    return '%d%02d%02d' % (year, month, day)


def next_period(d_str: str) -> str:
    return period_delta(d_str, 1)


def period_delta(d_str: str, delta: int) -> str:
    if delta == 0:
        return d_str
    year = int(d_str[0:4])
    month = int(d_str[4:6])
    step = 3
    if delta < 0:
        step = -3
        delta = abs(delta)
    for x in range(delta):
        month = month + step
        if month == 0:
            month = 12
            year = year - 1
        elif month == 15:
            month = 3
            year = year + 1
    return get_period(year, month)


def q_format_period(period: str) -> str:
    year = period[0:4]
    q = get_quarter_num(period)
    return '%sQ%d' % (year, q)


def q4_last_year(period: str) -> str:
    year = period[0:4]
    return get_period(int(year) - 1, 12)


def latest_period_date(dt: str) -> str:
    """
    根据日期返回之前最近的财报季度日期
    :param dt: 日期
    :return: 0331, 0630, 0930, 1231
    """
    year = int(dt[0:4])
    month = int(dt[4:6])
    while month != 3 and month != 6 and month != 9 and month != 12:
        month = month - 1
        if month == 0:
            month = 12
            year = year - 1

    return get_period(year, month)


def is_valid_dt(dt: str) -> bool:
    """
    判断是否合格的日期格式 yyyyMMdd
    :param dt: 日期
    :return: bool
    """
    try:
        parse_str(dt)
        return True
    except Exception as e:
        return False


if __name__ == '__main__':
    print(is_valid_dt('20210228'))
