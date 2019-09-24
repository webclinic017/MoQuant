' Declaration of manipulate db'

from moquant.dbclient import DBClient
from moquant.utils.datetime import format_delta

basic_start_date = '19910101'


def fetch_from_date(table: str, date_field: str, ts_code: str):
    sql = 'select max(%s) as max_date from %s where ts_code=\'%s\'' % (date_field, table, ts_code)
    client = DBClient()
    max_date = client.execute_sql(sql).fetchone()['max_date']
    from_date = basic_start_date
    if not (max_date is None):
        from_date = format_delta(max_date, day_num=1)
    return from_date
