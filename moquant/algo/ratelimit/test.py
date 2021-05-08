import time

from moquant.algo.ratelimit import RateLimiter
from moquant.log import get_logger
from moquant.utils import threadpool

log = get_logger(__name__)


def test_func(r: RateLimiter, start_time, n):
    r.get('test', 1.2, 50)
    now = time.time()
    log.info('%d time, cost %.2f' % (n, now - start_time))


if __name__ == '__main__':
    start = time.time()
    rt = RateLimiter()
    for i in range(200):
        threadpool.submit(test_func, r=rt, start_time=start, n=i)
    threadpool.join()
