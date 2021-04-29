#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" DB Client """
from warnings import filterwarnings

import pymysql
import sqlalchemy.engine.url as url
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.engine import ResultProxy, RowProxy
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from moquant.log import get_logger
from moquant.utils.env_utils import to_echo_sql, get_env_value

log = get_logger(__name__)

filterwarnings('ignore', category=pymysql.Warning)


class DBClient(object):
    __engine: Engine = None
    __session_auto: Session = None
    __session: Session = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__inst'):
            pymysql.install_as_MySQLdb()
            cls.__inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
            engine_url = url.URL(
                drivername='mysql',
                host=get_env_value('DB_HOST'),
                port=get_env_value('DB_PORT'),
                username=get_env_value('DB_USER'),
                password=get_env_value('DB_PWD'),
                database=get_env_value('MQ_DB_SCHEMA'),
                query={'charset': 'utf8'}
            )
            cls.__inst.__engine = create_engine(engine_url, encoding='utf-8', echo=to_echo_sql())
            cls.__inst.__session_auto = sessionmaker(bind=cls.__inst.__engine, autocommit=True)
            cls.__inst.__session = sessionmaker(bind=cls.__inst.__engine, autocommit=False)
        return cls.__inst

    def get_engine(self):
        return self.__engine

    def store_dataframe(self, df: DataFrame, table: str, exists: str = 'append'):
        df.to_sql(table, self.__engine, if_exists=exists, index=False, method='multi')

    def execute_sql(self, sql: str) -> ResultProxy:
        con: Connection = self.__engine.connect()
        return con.execute(sql)

    def query_with_sql(self, sql: str, target) -> list:
        proxy_list = self.execute_sql(sql).fetchall()
        result = []
        for proxy_item in proxy_list:  # type: RowProxy
            item = target()
            for k in proxy_item.keys():
                setattr(item, k, proxy_item[k])
            result.append(item)
        return result

    # session is not thread-safe, create a new session for every call
    def get_session(self, is_auto_commit: bool = True) -> Session:
        return self.__session_auto() if is_auto_commit else self.__session()

    def batch_insert(self, to_insert: list, page_size: int = 1000):
        """
        批量插入数据
        :param to_insert: 需要插入的数据
        :param page_size: 每页数量 默认1000
        :return:
        """
        if len(to_insert) > 0:
            s: Session = self.get_session()
            page_list = []
            for i in to_insert:
                page_list.append(i)
                if len(page_list) == page_size:
                    s.bulk_save_objects(page_list)
                    page_list = []
            if len(page_list) > 0:
                s.bulk_save_objects(page_list)
            s.close()


db_client = DBClient()
