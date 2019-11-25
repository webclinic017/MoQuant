import json
from decimal import Decimal


class MqEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)

        super(MqEncoder, self).default(o)
