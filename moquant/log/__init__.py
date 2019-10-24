#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Log util """
import logging
import sys
from logging.handlers import RotatingFileHandler

from moquant.utils.env_utils import get_env_value

sys.setdefaultencoding( "utf-8" )
log_formatter = '%(asctime)s - %(levelname)s - %(message)s'
level = logging.INFO
stdout = logging.StreamHandler(sys.stdout)
file_name = get_env_value('LOG_FILE_NAME')
file = RotatingFileHandler(file_name if file_name is not None else "mq.log", "w", 10240)
logging.basicConfig(format=log_formatter, level=level, handlers=[stdout, file])


def get_logger(name: str):
    return logging.getLogger(name)
