from sqlalchemy.orm import Session

from moquant.algo.tree.avl import AvlTree, AvlTreeNode
from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_indicator import MqDailyIndicator


class MqDailyStore(object):

    def __init__(self):
        self.data = {}

    def get_tree(self, ts_code: str, name: str) -> AvlTree:
        if ts_code not in self.data:
            self.data[ts_code] = {}
        code_data = self.data[ts_code]
        if name not in code_data:
            code_data[name] = AvlTree()
        return code_data[name]

    def add(self, to_add: MqDailyIndicator):
        tree = self.get_tree(to_add.ts_code, to_add.name)
        tree.add(to_add)

    def val(self, node: AvlTreeNode):
        return node.value if node is not None else None

    def find_date_exact(self, ts_code: str, name: str, update_date: str) -> MqDailyIndicator:
        tree = self.get_tree(ts_code, name)
        max_to_find = MqDailyIndicator(update_date=update_date)
        target = tree.find_equal(max_to_find)
        return self.val(target)


def init_daily_store_by_date(ts_code, from_date=mq_calculate_start_date) -> MqDailyStore:
    store = MqDailyStore()
    session: Session = db_client.get_session()
    arr = session.query(MqDailyIndicator).filter(MqDailyIndicator.ts_code == ts_code,
                                                 MqDailyIndicator.update_date >= from_date).all()
    session.close()
    for i in arr:
        store.add(i)
    return store
