#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
from argparse import Namespace
from typing import Optional

from sanic import Sanic

from core.servers.log import ensure_logging_config
from core.servers.start_app import create_app
from conf.settings import (

    LOGGER,
)

ensure_logging_config(LOGGER)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='snic-web')
    subparsers = parser.add_subparsers(dest='command')

    # run-server 子命令
    run_parser = subparsers.add_parser('run-server', help='run server')
    run_parser.add_argument('-c', '--config', required=True, help='config file path')

    # rsa-generate 子命令
    rsa_generate_parser = subparsers.add_parser('rsa-generate', help='rsa generate')
    rsa_generate_parser.add_argument('-p', '--path', required=True, help='generate path')

    # start-app 子命令
    start_parser = subparsers.add_parser('start-app', help='start app')
    start_parser.add_argument('-n', '--name', required=True, help='app name')

    return parser.parse_args()


class ManagementUtility:
    args: Optional[Namespace] = None
    name: str = "sanic-web"
    host: str = "0.0.0.0"
    port: int = 9815
    debug: bool = True
    workers: int = 1

    cors: bool = True

    def __init__(self):
        self.args = parse_args()

    def default_app(self):
        return None, self.host, self.port, self.debug, self.workers

    def execute(self) -> (Optional[Sanic], str, int, bool, int):
        """"""
        if self.args.command == 'run-server':
            pass
        elif self.args.command == 'rsa-generate':
            pass
        elif self.args.command == 'start-app':
            create_app(self.args.name).unwrap()
            return self.default_app()


def execute_from_command() -> (Optional[Sanic], str, int, bool, int):
    utility = ManagementUtility()
    return utility.execute()
