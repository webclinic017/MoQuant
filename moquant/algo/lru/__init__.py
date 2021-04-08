class LruItem(object):

    def __init__(self,
                 k: dict(type=str, help='key'),
                 v: dict(type=object, help='缓存对象')):
        self.key: str = k
        self.value: object = v
        self.prev: LruItem = None
        self.next: LruItem = None


class LruCache(object):

    def __init__(self, size: dict(type=int, help='缓存集大小')):
        self.kv: dict = {}
        self.max_size: int = size
        self.head: LruItem = None
        self.tail: LruItem = None

    def put(self,
            key: dict(type=str, help='缓存key'),
            value: dict(type=object, help='缓存对象')):

        if key in self.kv:
            item: LruItem = self.kv[key]
            item.value = value
            return

        if self.max_size == len(self.kv):
            self.pop()

        to_put: LruItem = LruItem(key, value)
        self.kv[key] = to_put
        self.tail.next = to_put
        to_put.prev = self.tail
        self.tail = to_put

    def pop(self):
        """
        将head清除掉
        """
        if self.head is None:
            return

        self.kv.pop(self.head.key)
        self.head = self.head.next
        self.head.prev = None

    def get(self,
            key: dict(type=str, help='缓存key')):
        """
        获取某个缓存，并放置到队尾
        """
        if key not in self.kv:
            return None

        to_get: LruItem = self.kv[key]
        prev_i: LruItem = to_get.prev
        next_i: LruItem = to_get.next

        if prev_i is None:
            if next_i is None:
                # 只有一个元素，没必要换位置
                return to_get
            else:
                # 换个头
                self.head = next_i
                next_i.prev = None
        else:
            # 前后拼接
            prev_i.next = next_i
            next_i.prev = prev_i

        # 把节点放到末尾
        self.tail.next = to_get
        to_get.prev = self.tail
        to_get.next = None
        self.tail = to_get

        return to_get
