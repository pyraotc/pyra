#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import importlib
from sanic import Sanic, Blueprint
from result import Result, Ok, Err
from sanic_ext import Extend
from sanic_compress import Compress
from tortoise.contrib.sanic import register_tortoise
from typing import Dict

from rcc.config import (
    INSTALL_APPS,
    VIEWS_DIR
)


def tortoise(app: Sanic, addr: str, modules: Dict, generate_schemas: bool = True) -> Result[bool, Exception]:
    """初始化ORM"""
    try:
        model_list = []
        for app_name, model_paths in modules.items():
            model_list.extend(model_paths)
        model_list = list(set(model_list))
        register_tortoise(
            app,
            modules={
                'models': model_list
            },
            db_url=addr,
            generate_schemas=generate_schemas,
        )
        return Ok(True)
    except Exception as exc:
        return Err(exc)


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


def discover_modules() -> Result[Dict, Exception]:
    """获取模型"""
    models = {}
    for app_path in INSTALL_APPS:
        app_name = app_path.split('.')[-1]
        if app_name:
            try:
                # 动态导入models模块
                models_module = __import__(f"{app_path}.models", fromlist=[''])
                has_models = False
                # 获取模块的所有属性
                module_dict = models_module.__dict__
                for key, value in module_dict.items():
                    if not key.startswith('__') and not isinstance(value, type(__import__('sys'))):
                        if isinstance(value, type):
                            has_models = True
                            break
                        elif hasattr(value, '__module__'):
                            if value.__module__.startswith(app_path):
                                has_models = True
                                break
                if has_models:
                    models[app_name] = [f"{app_path}.models"]
            except Exception as exc:
                return Err(exc)
    return Ok(models)


def get_tortoise_url() -> Result[str, Exception]:
    """获取db_url"""
    from core.conf import settings
    max_size = settings.get_int("DATABASE.MAX_SIZE", 10)
    min_size = settings.get_int("DATABASE.MIN_SIZE", 1)
    charset = settings.get_str("DATABASE.CHARSET", "utf8mb4")
    host = settings.get_str("DATABASE.HOST", None)
    port = settings.get_int("DATABASE.PORT", None)
    username = settings.get_str("DATABASE.USERNAME", None)
    password = settings.get_str("DATABASE.PASSWORD", None)
    name = settings.get_str("DATABASE.NAME", None)

    match settings.get("DATABASE.ENGINE"):
        case "pgsql" | "polar":
            return Ok(
                f"postgres://{username}:{password}@{host}:{port}/{name}?max_size={max_size}&min_size={min_size}")
        case "mysql":
            return Ok(
                f"mysql://{username}:{password}@{host}:{port}/{name}?max_size={max_size}&min_size={min_size}&charset={charset}")
        case _:
            return Err(Exception(f"{settings.get('DATABASE.ENGINE')} nonsupport"))


def setup(app: Sanic) -> Result[bool, Exception]:
    try:
        from core.conf import settings
        app.config.update(settings.get_dict("CONFIG", {}))
        app.ctx.version = '2.2.1'

        Extend(app)
        Compress(app)

        # 蓝图注册
        discover_blueprints(app)

        # 注册模型
        modules = discover_modules().unwrap()
        tortoise(app, get_tortoise_url().unwrap(), modules, settings.get_bool("DATABASE.GENERATE_SCHEMAS"))

        app.ext.openapi.describe(
            title="Sanic Web API",
            version='2.2.1',
            description="Sanic Web API",
        )
        return Ok(True)
    except Exception as exc:
        return Err(exc)
