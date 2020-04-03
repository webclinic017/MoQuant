from moquant.algo.tree.avl import AvlTree, AvlTreeNode
from moquant.dbclient.mq_quarter_index import MqQuarterIndex


class MqQuarterStore(object):

    def __init__(self):
        self.data = {}

    def get_tree(self, ts_code: str, name: str) -> AvlTree:
        if ts_code not in self.data:
            self.data[ts_code] = {}
        code_data = self.data[ts_code]
        if name not in code_data:
            code_data[name] = AvlTree()
        return code_data[name]

    def add(self, to_add: MqQuarterIndex):
        tree = self.get_tree(to_add.ts_code, to_add.name)
        tree.add(to_add)

    def val(self, node: AvlTreeNode):
        return node.value if node is not None else None

    def find_period_latest(self, ts_code: str, name: str, period: str) -> MqQuarterIndex:
        tree = self.get_tree(ts_code, name)
        max_to_find = MqQuarterIndex(period=period, update_date='99999999')
        target = tree.find_max_under(max_to_find)
        return self.val(target)

    def find_period_exact(self, ts_code: str, name: str, period: str, update_date: str) -> MqQuarterIndex:
        tree = self.get_tree(ts_code, name)
        max_to_find = MqQuarterIndex(period=period, update_date=update_date)
        target = tree.find_equal(max_to_find)
        return self.val(target)