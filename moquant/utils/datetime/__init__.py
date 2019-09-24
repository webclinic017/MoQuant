import datetime


def format_date(date: datetime, d_format: str = '%Y%m%d') -> str:
    return datetime.datetime.strftime(date, d_format)


def format_delta(d_str: str, d_format: str = '%Y%m%d', day_num: int = 0) -> str:
    d: datetime = parse_str(d_str, d_format)
    return format_date(d + datetime.timedelta(days=day_num))


def get_current_dt() -> str:
    return format_date(datetime.datetime.now())


def parse_str(d_str: str, d_format: str = '%Y%m%d') -> datetime:
    return datetime.datetime.strptime(d_str, d_format)
