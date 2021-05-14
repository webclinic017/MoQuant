from moquant.scripts.strategy import down_gap
from moquant.utils import date_utils


def generate_share_list(dt: str):
    """
    :param dt: 生成对应日期
    :return:
    """
    down_gap.run(dt)


if __name__ == '__main__':
    generate_share_list(date_utils.get_current_dt())
