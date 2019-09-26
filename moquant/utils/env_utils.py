import os


def get_env_value(key: str) -> str:
    return os.getenv(key)


def to_echo_sql() -> bool:
    return get_env_value('ECHO_SQL') == '1'


def pass_fetch_basic() -> bool:
    return get_env_value('PASS_FETCH_BASIC') == '1'
