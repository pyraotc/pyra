#!/usr/bin/env python
# -*- coding: utf-8 -*-
from result import Result, Ok, Err
from sanic.request import Request
from typing import Optional, Any, Literal

from core.reflect.model import TortoiseReflect


def client_info(request: Request) -> tuple:
    """获取客户端信息"""
    # 获取IP地址（考虑代理情况）
    ip_address = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.ip))
    if isinstance(ip_address, str) and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # 获取User-Agent
    user_agent = request.headers.get('User-Agent', 'Unknown')

    return ip_address, user_agent


class TortoiseLoggerReflect(TortoiseReflect):

    @classmethod
    async def create_log(cls, request: Request,
                         log_type: Literal['user', 'system'],
                         title: str,
                         content: str,
                         is_success: bool = True,
                         user: Optional[Any] = None,
                         error_message: Optional[str] = None,
                         metadata: Optional[Any] = None) -> Result[bool, Exception]:
        """
        :param log_type:
        :param request: sanic request
        :param title: log title
        :param content:  log content
        :param is_success:
        :param user:  writer log user
        :param error_message:
        :param metadata: other log
        :return:
        """
        try:
            ip_address, user_agent = client_info(request)
            user_log_result = await cls.create("logger", **{
                'log_type': log_type,
                'title': title,
                'content': content,
                'user': user,
                'metadata': metadata,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'is_success': is_success,
                'error_message': error_message
            })
            if not user_log_result.is_ok():
                return Err(user_log_result.err_value)
            return Ok(True)
        except Exception as exc:
            return Err(exc)
