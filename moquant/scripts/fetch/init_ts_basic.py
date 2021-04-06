from sqlalchemy.orm import Session

from dbclient import db_client
from moquant.dbclient.ts_basic import TsBasic
from tsclient import ts_client


def init():
    session: Session = db_client.get_session()
    session.query(TsBasic).delete()

    stock_data = ts_client.fetch_all_stock()

    if not stock_data.empty:
        db_client.store_dataframe(stock_data, TsBasic.__tablename__)
