from moquant.dbclient import db_client


def clear_duplicate_report_sql(table: str) -> str:
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
                select ts_code, end_date, max(id) as id
                from %s 
                group by ts_code, end_date having count(0) > 1
            ) to_keep
            left join %s ts
            on to_keep.ts_code = ts.ts_code and to_keep.end_date = ts.end_date and to_keep.id != ts.id
        ) tmp
    )
    """ % (table, table, table)


def clear():
    db_client.execute_sql(clear_duplicate_report_sql('ts_income'))
    db_client.execute_sql(clear_duplicate_report_sql('ts_balance_sheet'))
    db_client.execute_sql(clear_duplicate_report_sql('ts_cash_flow'))
    db_client.execute_sql(clear_duplicate_report_sql('ts_forecast'))
    db_client.execute_sql(clear_duplicate_report_sql('ts_express'))


if __name__ == '__main__':
    clear()
