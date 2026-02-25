#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.config
from result import Result, Ok, Err
from pathlib import Path


def ensure_log_directory(conf: dict) -> Result[bool, Exception]:
    """配置日志"""
    if conf.get("handlers") and "file" in conf["handlers"]:
        file_handler_config = conf["handlers"]["file"]

        # 获取日志文件路径
        log_file_path = file_handler_config.get("filename")

        if log_file_path:
            # 如果是字符串路径，转换为Path对象
            if isinstance(log_file_path, str):
                log_file_path = Path(log_file_path)

            # 获取日志文件所在目录
            log_dir = log_file_path.parent

            # 如果目录不存在，创建它
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    return Err(exc)
    return Ok(True)


def ensure_logging_config(conf: dict) -> Result[bool, Exception]:
    """初始化日志配置"""
    try:
        ensure_log_directory(conf).unwrap()
        logging.config.dictConfig(conf)
    except Exception as exc:
        return Err(exc)
