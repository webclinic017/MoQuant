from moquant.algo.tree import TreeNode


class AvlTreeNode(TreeNode):

    def __init__(self, v):
        super(AvlTreeNode, self).__init__(v)
        self.left: AvlTreeNode = None
        self.right: AvlTreeNode = None
        self.height: int = 1

    def update_height(self):
        left_height = self.left.height if self.left is not None else 0
        right_height = self.right.height if self.right is not None else 0
        self.height = max(left_height, right_height) + 1



class AvlTree(object):

    def __init__(self):
        self.root = None

    def add(self, value: object):
        node = AvlTreeNode(value)
        if self.root is None:
            self.root = node
        else:
            self._add(self.root, to_add=node)

    def _add(self, current: AvlTreeNode, to_add: AvlTreeNode):
