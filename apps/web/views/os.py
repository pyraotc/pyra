#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import platform
import time
from datetime import datetime
from sanic import Blueprint
from sanic_ext import openapi
from sanic.response import json

logger = logging.getLogger("tomcat")

os_bp = Blueprint('os', url_prefix='')


def _format_uptime(seconds):
    """将秒数转换为人类可读的时间格式"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:  # 至少显示秒数
        parts.append(f"{seconds}s")

    return " ".join(parts)


@os_bp.get('/ping')
@openapi.tag('os')
@openapi.summary('健康检查接口')
@openapi.description('用于检查服务是否正常运行，返回服务器状态和时间信息')
@openapi.response(200, {
    "status": str,
    "timestamp": str,
    "server_time": str,
    "uptime": float,
    "service": str,
    "environment": str
}, description="健康检查成功响应")
async def ping(request):
    """
        健康检查端点

        用于：
        1. 监控系统健康状态
        2. 负载均衡器健康检查
        3. 服务可用性验证
        """
    try:
        # 计算服务运行时间（如果有应用启动时间记录的话）
        start_time = getattr(request.app, 'start_time', time.time())
        uptime = time.time() - start_time

        response_data = {
            "status": "healthy",
            "message": "Service is running normally",
            "timestamp": datetime.now().isoformat(),
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime_seconds": round(uptime, 2),
            "uptime_human": _format_uptime(uptime),
            "service": "sanic-api",
            "environment": request.app.config.get("ENVIRONMENT", "development"),
            "version": getattr(request.app.ctx, 'version', '1.0.0'),
            "python_version": platform.python_version(),
            "platform": platform.system()
        }

        return json(response_data, status=200)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        error_response = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "sanic-api"
        }
        return json(error_response, status=503)
