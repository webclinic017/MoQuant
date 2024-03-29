from moquant.scripts.strategy import down_gap, grow, dividend


def generate_strategy_pool(dt: str):
    """
    :param dt: 生成对应日期
    :return:
    """
    down_gap.run(dt)
    grow.run(dt)
    dividend.run(dt)


if __name__ == '__main__':
    generate_strategy_pool('20210618')
