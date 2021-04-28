from moquant.dbclient import db_client
from moquant.log import get_logger

log = get_logger(__name__)


def clear_duplicate_report_sql(table: str, ts_code: str) -> str:
    code_where = '1=1' if ts_code is None else 'ts_code = \'%s\'' % ts_code
    table_with_where = table if ts_code is None else '%s where ts_code = \'%s\'' % (table, ts_code)
    return """
    delete a from %s a
    left join
    (
    select ts_code as code, mq_ann_date, end_date, max(id) as id
    from %s
    group by ts_code, mq_ann_date, end_date
    having count(0) > 1
    ) b
    on a.ts_code=b.code and a.mq_ann_date=b.mq_ann_date and a.end_date=b.end_date and a.id != b.id
    where %s and b.code is not null
    """ % (table, table_with_where, code_where)


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
    code_where = '1=1' if ts_code is None else 'ts_code = \'%s\'' % ts_code
    table_with_where = table if ts_code is None else '%s where ts_code = \'%s\'' % (table, ts_code)
    return """
    delete ts from %s ts
    left join
    (
        select ts_code as code, end_date, ann_date, max(id) as id
        from %s 
        group by ts_code, end_date, ann_date having count(0) > 1
    ) to_keep
    on to_keep.code = ts.ts_code and to_keep.end_date = ts.end_date 
    and to_keep.ann_date = ts.ann_date
    and to_keep.id != ts.id
    where %s and to_keep.id is not null        
    """ % (table, table_with_where, code_where)


def clear_duplicate_dividend(ts_code):
    code_where = '1=1' if ts_code is None else 'ts_code = \'%s\'' % ts_code
    return """
    delete source from ts_dividend source
    left join
    (
        select ts_code as code, imp_ann_date, div_proc, ex_date, min(end_date) as end_date
        from ts_dividend where %s
        group by ts_code, imp_ann_date, div_proc, ex_date
        having count(0) > 1
    ) to_keep
    on to_keep.code=source.ts_code
            and to_keep.imp_ann_date=source.imp_ann_date
            and to_keep.div_proc=source.div_proc
            and to_keep.ex_date=source.ex_date
            and to_keep.end_date != source.end_date
    where %s and to_keep.end_date is not null
    """ % (code_where, code_where)


def clear_duplicate_dividend_2(ts_code):
    code_where = '1=1' if ts_code is None else 'ts_code = \'%s\'' % ts_code
    return """
    delete source from ts_dividend source
    left join
    (
        select ts_code as code, end_date, imp_ann_date, div_proc, max(id) as id
        from ts_dividend where %s
        group by ts_code, end_date, imp_ann_date, div_proc
        having count(0) > 1
    ) to_keep
    on to_keep.code=source.ts_code
            and to_keep.end_date=source.end_date
            and to_keep.imp_ann_date=source.imp_ann_date
            and to_keep.div_proc=source.div_proc
            and to_keep.id!=source.id
    where %s and to_keep.id is not null
    """ % (code_where, code_where)


def clear(ts_code: str = None):
    db_client.execute_sql(clear_duplicate_report_sql('ts_income', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_balance_sheet', ts_code))
    db_client.execute_sql(clear_duplicate_adjust_report_with('ts_income', ts_code))
    db_client.execute_sql(clear_duplicate_adjust_report_with('ts_balance_sheet', ts_code))
    db_client.execute_sql(clear_duplicate_report_sql('ts_cash_flow', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_forecast', ts_code))
    db_client.execute_sql(clear_duplicate_forecast('ts_express', ts_code))
    db_client.execute_sql(clear_duplicate_dividend(ts_code))
    db_client.execute_sql(clear_duplicate_dividend_2(ts_code))
    log.info('clear duplicate %s' % ts_code)


if __name__ == '__main__':
    clear()
