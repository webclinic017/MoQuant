from moquant.algo.tree import TreeNode


class AvlTreeNode(TreeNode):

    def __init__(self, v):
        super(AvlTreeNode, self).__init__(v)
        self.left: AvlTreeNode = None
        self.right: AvlTreeNode = None
        self.height: int = 1

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __le__(self, other):
        return self.value <= other.value

    def __lt__(self, other):
        return self.value < other.value

    def update_height(self):
        left_height = self.left.height if self.left is not None else 0
        right_height = self.right.height if self.right is not None else 0
        self.height = max(left_height, right_height) + 1


class AvlTree(object):

    def __init__(self):
        self.root = None

    def add(self, value: object):
        node = AvlTreeNode(value)
        self.root = self._add(self.root, to_add=node)

    def _add(self, current: AvlTreeNode, to_add: AvlTreeNode):
        if current is None:
            return to_add
        if to_add < current:
            current.left = self._add(current.left, to_add)
        elif to_add > current:
            current.right = self._add(current.right, to_add)
        else:  # 已存在时不再插入
            return current

        self.update_height(current)
        bl = self.get_balance(current)
        if bl > 1 and self.get_balance(current.left) > 0:
            return self.right_rotate(current)
        elif bl < -1 and self.get_balance(current.right) < 0:
            return self.left_rotate(current)
        elif bl > 1 and self.get_balance(current.left) < 0:
            current.left = self.left_rotate(current.left)
            return self.right_rotate(current)
        elif bl < -1 and self.get_balance(current.right) > 0:
            current.right = self.right_rotate(current.right)
            return self.left_rotate(current)
        else:
            return current

    def get_height(self, p: AvlTreeNode):
        if p is None:
            return 0
        return p.height

    def get_balance(self, p: AvlTreeNode):
        if p is None:
            return 0
        return self.get_height(p.left) - self.get_height(p.right)

    def update_height(self, p: AvlTreeNode):
        if p is not None:
            p.update_height()

    # LL - 右旋
    def right_rotate(self, p: AvlTreeNode):
        l: AvlTreeNode = p.left
        lr: AvlTreeNode = l.right
        l.right = p
        p.left = lr
        self.update_height(p)
        self.update_height(l)
        return l

    # RR - 左旋
    def left_rotate(self, p: AvlTreeNode):
        r: AvlTreeNode = p.right
        rl: AvlTreeNode = r.left
        r.left = p
        p.right = rl
        self.update_height(p)
        self.update_height(r)
        return r

    def find_max_under(self, val) -> AvlTreeNode:
        return self._find_max_under(self.root, val)

    def _find_max_under(self, current: AvlTreeNode, val) -> AvlTreeNode:
        if current is None:
            return None
        elif current.value == val:
            return current
        elif current.value < val:
            right_max = self._find_max_under(current.right, val)
            return right_max if right_max is not None else current
        else:
            return self._find_max_under(current.left, val)

    def find_equal(self, val) -> AvlTreeNode:
        return self._find_equal(self.root, val)

    def _find_equal(self, current: AvlTreeNode, val) -> AvlTreeNode:
        if current is None:
            return None
        elif current.value == val:
            return current
        elif current.value < val:
            return self._find_equal(current.right, val)
        else:
            return self._find_equal(current.left, val)