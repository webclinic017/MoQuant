#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Log util """
import logging
import sys

log_formatter = '%(asctime)s - %(levelname)s - %(message)s'
level = logging.INFO
stdout = logging.StreamHandler(sys.stdout)
logging.basicConfig(format=log_formatter, level=level, handlers=[stdout])


def get_logger(name: str):
    return logging.getLogger(name)
