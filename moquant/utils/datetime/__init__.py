import datetime


def format_date(date: datetime, d_format: str = '%Y%m%d') -> str:
    return datetime.datetime.strftime(date, d_format)


def format_delta(d_str: str, day_num: int = 0, d_format: str = '%Y%m%d') -> str:
    d: datetime = parse_str(d_str, d_format)
    return format_date(d + datetime.timedelta(days=day_num))


def get_current_dt() -> str:
    return format_date(datetime.datetime.now())


def parse_str(d_str: str, d_format: str = '%Y%m%d') -> datetime:
    return datetime.datetime.strptime(d_str, d_format)


def first_report_period(d_str: str, delta_year: int = 0) -> str:
    year_part = d_str[0:4]
    if delta_year != 0:
        year_int = int(year_part) + delta_year
        return '%d0331' % year_int
    else:
        return '%s0331' % year_part


def date_max(d_arr: list) -> str:
    ans = None
    for d_str in d_arr:
        if d_str is None:
            continue
        if ans is None or d_str > ans:
            ans = d_str
    return ans


def get_quarter_num(d_str: str) -> int:
    return (int(d_str[4:6]) - 1) // 3 + 1 if d_str is not None else 0
