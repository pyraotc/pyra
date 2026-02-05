#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sanic import Sanic
from tortoise.contrib.sanic import register_tortoise
from typing import Dict
from result import Result, Ok, Err


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
