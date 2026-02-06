#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import importlib
from sanic import Sanic, Blueprint
from result import Result, Ok, Err
from sanic_ext import Extend
from sanic_compress import Compress

from conf.settings import (
    INSTALL_APPS,
    VIEWS_DIR
)


def discover_blueprints(srv: Sanic):
    """注册蓝图"""
    for app_name in INSTALL_APPS:
        app_module_path = importlib.import_module(app_name).__path__[0]
        views_dir_path = os.path.join(app_module_path, VIEWS_DIR)
        if not os.path.exists(views_dir_path):
            continue
        for file_name in os.listdir(views_dir_path):
            if not file_name.endswith('.py') or file_name == '__init__.py':
                continue
            file_module_name = file_name[:-3]
            views_module_path = f'{app_name}.{VIEWS_DIR}.{file_module_name}'
            try:
                views_module = importlib.import_module(views_module_path)
                for var_name in dir(views_module):
                    if not var_name.endswith('_bp'):
                        continue
                    var_value = getattr(views_module, var_name)
                    if isinstance(var_value, Blueprint):
                        srv.blueprint(var_value)
            except ModuleNotFoundError:
                continue


def setup(app: Sanic) -> Result[bool, Exception]:
    try:
        from core.config import settings
        app.config.update(settings.get_dict("CONFIG", {}))
        app.ctx.version = '2.2.1'

        Extend(app)
        Compress(app)

        # 蓝图注册
        discover_blueprints(app)

        app.ext.openapi.describe(
            title="Sanic Web API",
            version='2.2.1',
            description="Sanic Web API",
        )
        return Ok(True)
    except Exception as exc:
        return Err(exc)
