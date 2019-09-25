from moquant.dbclient import db_client
from moquant.dbclient.ts_basic import StockBasic
from moquant.tsclient import ts_client


def init_stock_basic():
    stock_data = ts_client.fetch_all_stock()

    if not stock_data.empty:
        db_client.store_dataframe(stock_data, StockBasic.__tablename__)


if __name__ == '__main__':
    init_stock_basic()
