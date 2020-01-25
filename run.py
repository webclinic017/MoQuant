#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from moquant.log import get_logger
from moquant.scripts import clear_all_data, init_table, fetch_data, fetch_latest, download_pdf, calculate
from moquant.strategy import loopback
from moquant.utils import env_utils
from moquant.utils.date_utils import get_current_dt

log = get_logger(__name__)

if __name__ == '__main__':
    args = env_utils.get_args()

    if args.job == 'init':
        init_table.create_table()
    elif args.job == 'clear':
        clear_all_data.run(args.code)
    elif args.job == 'fetch_daily':
        fetch_data.run(args.code, args.date)
    elif args.job == 'fetch_latest':
        fetch_latest.run()
    elif args.job == 'recalculate':
        calculate.recalculate(args.code)
    elif args.job == 'df':
        download_pdf.forecast()
    elif args.job == 'sim':
        loopback.run_grow_strategy('20190101', get_current_dt())
    else:
        log.error("unsupported job [%s]" % args.job)
