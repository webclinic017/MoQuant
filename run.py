#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from moquant.log import get_logger
from moquant.scripts import clear_all_data, init_table, fetch_data, fetch_latest, recalculate, download_pdf
from moquant.utils import env_utils

log = get_logger(__name__)

if __name__ == '__main__':
    args = env_utils.get_args()

    if args.job == 'init':
        init_table.create_table()
    elif args.job == 'clear':
        clear_all_data.run(args.code)
    elif args.job == 'fetch_daily':
        fetch_data.run(args.code, args.to_date)
    elif args.job == 'fetch_latest':
        fetch_latest.run()
    elif args.job == 'recalculate':
        recalculate.run(args.code)
    elif args.job == 'df':
        download_pdf.forecast()
    else:
        log.error("unsupported job [%s]" % args.job)
