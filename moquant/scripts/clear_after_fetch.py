from moquant.dbclient import db_client
from moquant.log import get_logger

log = get_logger(__name__)


def clear_duplicate_report_sql(table: str, ts_code: str) -> str:
    table_with_where = table if ts_code is None else '%s where ts_code = \'%s\'' % (table, ts_code)
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
                select ts_code, end_date, mq_ann_date, report_type, max(id) as id
                from %s 
                group by ts_code, end_date, mq_ann_date, report_type having count(0) > 1
            ) to_keep
            left join (select * from %s) ts
            on to_keep.ts_code = ts.ts_code and to_keep.end_date = ts.end_date 
            and to_keep.mq_ann_date = ts.mq_ann_date
            and to_keep.report_type = ts.report_type
            and to_keep.id != ts.id
        ) tmp
    )
    """ % (table, table_with_where, table_with_where)


def clear_duplicate_adjust_report_with(table: str, ts_code: str) -> str:
    code_where = '1=1' if ts_code is None else 'ts_code = \'%s\'' % ts_code
    table_with_where = table if ts_code is None else '%s where ts_code = \'%s\'' % (table, ts_code)
    return """
    delete a from %s a
    left join
    (
    select ts_code as code, mq_ann_date, end_date
    from %s
    group by ts_code, mq_ann_date, end_date
    having count(0) > 1
    ) b
    on a.ts_code=b.code and a.mq_ann_date=b.mq_ann_date and a.end_date=b.end_date
    where %s and a.report_type=4 and b.code is not null
    """ % (table, table_with_where, code_where)


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
                select ts_code, end_date, ann_date, max(id) as id
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


def clear_duplicate_dividend(ts_code):
    return """
    delete from ts_dividend
    where id in
    (
        select id
        from
        (
            select source.id
            from
            (
                select ts_code, end_date, ann_date, div_proc, max(id) as id
                from ts_dividend
                where %s
                group by ts_code, end_date, ann_date, div_proc
                having count(0) > 1
            ) to_keep
            left join ts_dividend source
            on to_keep.ts_code=source.ts_code
            and to_keep.end_date=source.end_date
            and to_keep.ann_date=source.ann_date
            and to_keep.div_proc=source.div_proc
            and to_keep.id!=source.id
        ) tmp
    )
    """ % ('1=1' if ts_code is None else 'ts_code=\'%s\'' % ts_code)


def clear(ts_code: str):
    db_client.execute_sql(clear_duplicate_report_sql('ts_income', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_balance_sheet', ts_code))
    db_client.execute_sql(clear_duplicate_adjust_report_with('ts_income', ts_code))
    db_client.execute_sql(clear_duplicate_adjust_report_with('ts_balance_sheet', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_cash_flow', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_forecast', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_express', ts_code))
    db_client.execute_sql(clear_duplicate_dividend(ts_code))
    log.info('clear duplicate %s' % ts_code)


if __name__ == '__main__':
    clear()
