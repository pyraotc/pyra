#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
import os
from argparse import Namespace
from typing import Optional

from sanic import Sanic
from result import Result, Ok, Err

from utils.log import ensure_logging_config
from utils.app import create_app
from rcc.config import (
    LOGGER,
)

from core.conf import YamlLoader
from utils.web import setup

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


def generate_rsa_key(path: str) -> Result[bool, Exception]:
    try:
        from core.crypto.rsa import DEFAULT_EXPONENT, DEFAULT_SIZE, generate_keys, save_private_key, save_public_key
        keys_result = generate_keys(DEFAULT_SIZE, DEFAULT_EXPONENT)
        if not keys_result.is_ok():
            return Err(keys_result.err_value)
        keys = keys_result.ok_value
        save_private_key(os.path.join(path, 'private.pem'), keys[0]).unwrap()
        save_public_key(os.path.join(path, 'public.pem'), keys[1]).unwrap()
        logger.info(f"Generated RSA keys successfully -> {path}")
        return Ok(True)
    except Exception as exc:
        logger.error(exc)
        return Err(exc)


class ManagementUtility:
    args: Optional[Namespace] = None
    name: str = "sanic-web"
    host: str = "0.0.0.0"
    port: int = 85
    debug: bool = True
    workers: int = 1

    def __init__(self):
        self.args = parse_args()

    def default_app(self):
        return None, self.host, self.port, self.debug, self.workers

    def reset_server(self) -> Result[bool, Exception]:
        """"""
        from core.conf import settings as cfg
        try:
            self.name = cfg.get_str("NAME", "sanic-web")
            self.host = (lambda ip, default="0.0.0.0": ip if all(
                part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')) and len(
                ip.split('.')) == 4 else default)(
                cfg.get("SERVER.HOST", "0.0.0.0"))
            self.port = (lambda p, default=8000: int(p) if str(p).isdigit() and 0 <= int(p) <= 65535 else default)(
                cfg.get("SERVER.PORT", 8000))
            self.debug = cfg.get_bool("SERVER.DEBUG", False)
            self.workers = cfg.get_int("SERVER.WORKERS", 1)
            return Ok(True)
        except Exception as exc:
            return Err(exc)

    def execute(self) -> (Optional[Sanic], str, int, bool, int):
        """"""
        from tokio.tasks import Task

        if self.args.command == 'run-server':
            YamlLoader.open(self.args.config).unwrap().glob()
            self.reset_server().unwrap()

            app = Sanic(self.name)
            setup(app).unwrap()
            app.ctx.task = Task()
            return app, self.host, self.port, self.debug, self.workers
        elif self.args.command == 'rsa-generate':
            generate_rsa_key(self.args.path).unwrap()
            return self.default_app()
        elif self.args.command == 'start-app':
            create_app(self.args.name).unwrap()
            return self.default_app()


def execute_from_command() -> (Optional[Sanic], str, int, bool, int):
    utility = ManagementUtility()
    return utility.execute()
