from moquant.algo.tree import TreeNode


class BinaryTreeNode(TreeNode):

    def __init__(self, v):
        super(BinaryTreeNode, self).__init__(v)
        self.left = None
        self.right = None


class BinaryTree(object):

    def __init__(self):
        self.root = None
