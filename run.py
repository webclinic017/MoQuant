#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getopt
import sys

from moquant.scripts import clear_all_data, init_table, fetch_data, cal_mq_daily


def usage():
    print("-j job init_table, clear_all_data, fetch_data, cal_mq_basic")
    print("-c ts_code Eg. 000001.SZ")


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "hj:c:")
    job_name = None
    ts_code = None
    for op, value in opts:
        if op == "-j":
            job_name = value
        elif op == "-c":
            ts_code = value
        elif op == "-h":
            usage()
            sys.exit()
    if job_name == 'init_table':
        init_table.create_table()
    elif job_name == 'clear_all_data':
        clear_all_data.run(ts_code)
    elif job_name == 'fetch_data':
        fetch_data.run(ts_code)
    elif job_name == 'cal_mq_daily':
        cal_mq_daily.run(ts_code)
    else:
        print("unsupported job")
