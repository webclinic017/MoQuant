#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To init table, will not create if table exists """

import moquant.dbclient as client
from moquant.dbclient.base import Base


def create_table():
    engine = client.db_client.get_engine()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_table()
