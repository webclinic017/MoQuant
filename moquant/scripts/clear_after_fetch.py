from moquant.dbclient import db_client
from moquant.log import get_logger

log = get_logger(__name__)


def clear_duplicate_report_sql(table: str, ts_code: str) -> str:
    return """
    delete from %s
    where id in
    (
        select id
        from (
            select 
                ts.id
            from
            (
                select ts_code, end_date, f_ann_date, report_type, min(id) as id
                from %s 
                group by ts_code, end_date, f_ann_date, report_type having count(0) > 1
            ) to_keep
            left join %s ts
            on to_keep.ts_code = ts.ts_code and to_keep.end_date = ts.end_date 
            and to_keep.f_ann_date = ts.f_ann_date
            and to_keep.report_type = ts.report_type
            and to_keep.id != ts.id
        ) tmp
    )
    """ % (table, table if ts_code is None else table + ' where ts_code = \'%s\'' % ts_code, table)


def clear_duplicate_forecast(table: str, ts_code: str) -> str:
    return """
    delete from %s
    where id in
    (
        select id
        from (
            select 
                ts.id
            from
            (
                select ts_code, end_date, ann_date, min(id) as id
                from %s 
                group by ts_code, end_date, ann_date having count(0) > 1
            ) to_keep
            left join %s ts
            on to_keep.ts_code = ts.ts_code and to_keep.end_date = ts.end_date 
            and to_keep.ann_date = ts.ann_date
            and to_keep.id != ts.id
        ) tmp
    )
    """ % (table, table if ts_code is None else table + ' where ts_code = \'%s\'' % ts_code, table)


def clear(ts_code: str):
    db_client.execute_sql(clear_duplicate_report_sql('ts_income', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_balance_sheet', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_cash_flow', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_forecast', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_express', ts_code))
    log.info('clear duplicate report')


if __name__ == '__main__':
    clear()
