from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT, TIMESTAMP, text

from moquant.dbclient.base import Base


class MqShareNoteRelation(Base):
    __tablename__ = 'mq_share_note_relation'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    note_id = Column('note_id', BIGINT, primary_key=True, comment='日记ID')
    create_time = Column('create_time', TIMESTAMP, comment='创建时间',
                         server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column('update_time', TIMESTAMP, comment='更新时间',
                         server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
