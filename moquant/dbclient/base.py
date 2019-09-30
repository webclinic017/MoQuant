""" Common factory for declarative_base """

from sqlalchemy.ext.declarative import declarative_base


class MqAlchemyBase(object):
    def to_dict(self):
        return {key: value for (key, value) in self.items()}


Base = declarative_base(cls=MqAlchemyBase)
