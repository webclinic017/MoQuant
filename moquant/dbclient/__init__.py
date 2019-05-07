#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' DB Client '
__author__ = 'Momojie'

import json as json


class DBClient(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        info_file = open('./resources/db_info.json', encoding='utf-8')
        info_json = json.load(info_file)
        print(info_json)
