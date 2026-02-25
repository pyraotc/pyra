#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALL_APPS = [
    'apps.web',
]

VIEWS_DIR = 'views'

# ===================================================logger=============================================================

LOGGER_DIR = Path(os.environ.get("LOGGER_DIR", BASE_DIR / 'logs'))

LOGGER = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': sys.stdout
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': "ERROR",
            'formatter': 'detailed',
            'filename': str(LOGGER_DIR / 'pyra.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        },
        # 第三方库的日志级别控制
        'urllib3': {
            'level': 'WARNING',
            'propagate': True
        },
        'requests': {
            'level': 'WARNING',
            'propagate': True
        },
        'asyncio': {
            'level': 'WARNING',
            'propagate': True
        }
    }
}
