class SimOrder(object):
    __success: bool
    __msg: str
    __type: int # 0 sell 1 buy
    __ts_code: str
    __num: int
    __status: int  # 0 sent, 1 deal

    def __init__(self, type: int, ts_code: str, num: int, success: bool=True, msg: str=''):
        self.__type = type
        self.__ts_code = ts_code
        self.__num = num
        self.__success = success
        self.__msg = msg
        self.__status = 0
