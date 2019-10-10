from sqlalchemy import Column, String, Boolean

from moquant.dbclient.base import Base


class MqSysParam(Base):
    __tablename__ = 'mq_sys_param'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    param_key = Column('param_key', String(20), primary_key=True, comment='键')
    param_value = Column('param_value', String(100), comment='值')
    param_remark = Column('param_remark', String(50), comment='备注')
