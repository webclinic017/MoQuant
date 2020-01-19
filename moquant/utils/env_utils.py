import argparse
import os

parser = argparse.ArgumentParser(description='MoQuant')
parser.add_argument('--job', metavar='JOB', default='fetch_daily', help='运行的任务 init, fetch_daily, fetch_latest, clear')
parser.add_argument('--code', metavar='N', help='需要运行的ts_code')
parser.add_argument('--to-date', metavar='N', help='需要执行到的日期，默认最新')
parser.add_argument('--parallel', metavar='PARALLEL', default='1', help='是否并发执行')


def get_args():
    return parser.parse_args()


def parallel() -> bool:
    return get_args().parallel == '1'


def get_env_value(key: str) -> str:
    return os.getenv(key)


def to_echo_sql() -> bool:
    return get_env_value('ECHO_SQL') == '1'


def pass_fetch_basic() -> bool:
    return get_env_value('PASS_FETCH_BASIC') == '1'
