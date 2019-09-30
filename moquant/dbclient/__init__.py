#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" DB Client """
import json as json

import pymysql
import sqlalchemy.engine.url as url
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.engine import ResultProxy
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from moquant.log import get_logger
from moquant.utils import json_utils
from moquant.utils.env_utils import to_echo_sql

log = get_logger(__name__)


class DBClient(object):
    __engine: Engine = None
    __session_auto: Session = None
    __session: Session = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__inst'):
            pymysql.install_as_MySQLdb()
            cls.__inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
            info_json = json_utils.from_file('/resources/db_info.json')
            engine_url = url.URL(
                drivername='mysql',
                host=info_json['host'],
                port=info_json['port'],
                username=info_json['user'],
                password=info_json['password'],
                database=info_json['database'],
                query={'charset': 'utf8'}
            )
            log.info('Database config: %s' % json.dumps(info_json))
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

    # session is not thread-safe, create a new session for every call
    def get_session(self, is_auto_commit: bool = True) -> Session:
        return self.__session_auto() if is_auto_commit else self.__session()


db_client = DBClient()
