from moquant.algo.tree.avl import AvlTree, AvlTreeNode
from moquant.dbclient.mq_quarter_indicator import MqQuarterIndicator


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

    def add(self, to_add: MqQuarterIndicator):
        tree = self.get_tree(to_add.ts_code, to_add.name)
        tree.add(to_add)

    def val(self, node: AvlTreeNode):
        return node.value if node is not None else None

    def find_period_latest(self, ts_code: str, name: str, period: str, update_date: str='99999999') -> MqQuarterIndicator:
        tree = self.get_tree(ts_code, name)
        max_to_find = MqQuarterIndicator(period=period, update_date=update_date)
        target = tree.find_max_under(max_to_find)
        ret: MqQuarterIndicator = self.val(target)
        return ret if ret is not None and ret.period == period else None

    def find_period_exact(self, ts_code: str, name: str, period: str, update_date: str) -> MqQuarterIndicator:
        tree = self.get_tree(ts_code, name)
        max_to_find = MqQuarterIndicator(period=period, update_date=update_date)
        target = tree.find_equal(max_to_find)
        return self.val(target)