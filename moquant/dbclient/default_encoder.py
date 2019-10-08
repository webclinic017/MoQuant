import json
from decimal import Decimal

from sqlalchemy.ext.declarative import DeclarativeMeta

from moquant.dbclient.mq_daily_basic import MqDailyBasic


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                if data is not None:
                    if isinstance(data, Decimal):
                        fields[field] = float(data)
                    else:
                        fields[field] = data
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


def test():
    obj = MqDailyBasic(ts_code='000001', close=11, is_trade_day=True)
    print(json.dumps(obj, cls=AlchemyEncoder))


if __name__ == "__main__":
    test()
