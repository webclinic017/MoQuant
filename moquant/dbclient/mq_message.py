from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqMessage(Base):
    __tablename__ = 'mq_message'
    __table_args__ = (
        Index('msg_type', 'msg_type'),
        Index('code', 'ts_code'),
        Index('pub_date', 'pub_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    msg_type = Column('msg_type', INT, comment='消息种类 1-业绩')
    message = Column('message', String(100), comment='消息体')
    pub_date = Column('pub_date', String(10), comment='消息发布日期')
