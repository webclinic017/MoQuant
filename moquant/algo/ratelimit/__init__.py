import math
import time
from multiprocessing import Lock

from moquant.log import get_logger

log = get_logger(__name__)


class RateLimiter(object):

    def __init__(self):
        """
        简易的令牌桶，令牌最大数量，生成速度皆由调用方定义
        """
        self.__new_lock: Lock = Lock()
        self.__locks: dict = {}

        self.__left: dict = {}
        self.__last_time: dict = {}

    def get(self, name: str, rate: float, max_num: int):
        """
        获取令牌，会阻塞等待
        :param name: 方法名，每个方法会记录自己的令牌数
        :param rate: 生成速率，每个令牌需要多少秒去生成 = 1 / qps
        :param max_num: 该方法允许的最大令牌数
        :return:
        """
        if name not in self.__locks:
            self.__new_lock.acquire()
            try:
                if name not in self.__locks:
                    self.__locks[name] = Lock()
            finally:
                self.__new_lock.release()

        while True:
            get: bool = False
            l: Lock = self.__locks[name]
            l.acquire()
            try:
                now = time.time()

                if name not in self.__last_time:
                    self.__last_time[name] = now
                if name not in self.__left:
                    self.__left[name] = max_num

                # 令牌未满，先补
                if self.__left[name] < max_num:
                    time_diff = now - self.__last_time[name]
                    to_add: int = math.floor(time_diff / rate)
                    # 距离上次时间足够增加新的令牌
                    if to_add > 0:
                        self.__last_time[name] = self.__last_time[name] + rate * to_add
                        new_num = self.__left[name] + to_add
                        if new_num > max_num:
                            new_num = max_num
                        self.__left[name] = new_num

                # 处理增加令牌后，有令牌可以消耗
                if self.__left[name] > 0:
                    self.__left[name] = self.__left[name] - 1
                    get = True
            finally:
                l.release()

            if get:
                break
            else:
                time.sleep(rate)
        return True
