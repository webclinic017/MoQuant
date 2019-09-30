from sqlalchemy.orm import Session

from moquant.dbclient import db_client
from moquant.dbclient.mq_basic_all import MqStockBasicAll


def get_mq_basic(ts_code: str) -> MqStockBasicAll:
    session: Session = db_client.get_session()
    result = session.query(MqStockBasicAll).filter(MqStockBasicAll.ts_code == ts_code) \
        .order_by(MqStockBasicAll.date.desc()).limit(1).all()
    return [row.to_dict() for row in result]
