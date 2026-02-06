#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sanic import Sanic
from result import Result, Ok, Err
from sanic_ext import Extend
from sanic_compress import Compress


def setup(app: Sanic) -> Result[bool, Exception]:
    try:
        from core.config import settings
        app.config.update(settings.get_dict("CONFIG", {}))

        Extend(app)
        Compress(app)

        app.ext.openapi.describe(
            title="Sanic Web API",
            version='2.2.1',
            description="Sanic Web API",
        )
        return Ok(True)
    except Exception as exc:
        return Err(exc)
