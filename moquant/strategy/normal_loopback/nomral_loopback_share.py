class NormalLoopbackShare(object):

    def __init__(self, ts_code: str, dt: str):
        """
        普通股池
        :param ts_code: 编码
        :param dt: 哪天要买入
        """
        self.ts_code = ts_code
        self.dt = dt
