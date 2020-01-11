from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT, TIMESTAMP, text

from moquant.dbclient.base import Base


class MqShareNote(Base):
    __tablename__ = 'mq_share_note'
    __table_args__ = (
        Index('code', 'ts_code', 'create_time'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    create_time = Column('create_time', TIMESTAMP, comment='创建时间',
                         server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column('update_time', TIMESTAMP, comment='更新时间',
                         server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    event_brief = Column('event_brief', String(1000), comment='事件简述')
    note_detail = Column('note_detail', String(1000), comment='笔记详情')
    note_conclusion = Column('note_conclusion', String(100), comment='笔记总结')
