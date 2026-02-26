#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from celery.schedules import crontab, schedule
from redisbeat.scheduler import RedisScheduler
from result import Result, Ok, Err

from schedule import app

logger = logging.getLogger(__name__)


class Task:
    """celery定时任务管理器"""

    def __init__(self, celery_app=None):
        """初始化任务管理器"""
        self.celery_app = celery_app or app
        self.scheduler = RedisScheduler(app=self.celery_app)

    def list(self) -> Result[Dict[str, Any], Exception]:
        """
        列出所有定时任务
        """
        try:
            return Ok(self.scheduler.list())
        except Exception as exc:
            return Err(exc)

    def export(self) -> Result[List[Dict[str, Any]], Exception]:
        """导出所有任务配置，用于备份"""
        try:
            tasks = self.scheduler.list()
            exported = []
            for name, info in tasks.items():
                exported.append({
                    'name': name,
                    'task': info.get("task", None),
                    'schedule': str(info.get("schedule", "")),
                    'args': info.get("args", []),
                    'kwargs': info.get("kwargs", {}),
                    'options': info.get("options", {}),
                    'enabled': info.get("enabled", True),
                })
            return Ok(exported)
        except Exception as exc:
            return Err(exc)

    def clear(self) -> Result[bool, Exception]:
        """清除所有定时任务"""
        try:
            tasks = self.scheduler.list()
            for name in tasks:
                self.scheduler.remove(name)
            return Ok(True)
        except Exception as exc:
            return Err(exc)

    def remove(self, name: str) -> Result[bool, Exception]:
        """
        删除某个定时任务
        :param name: 定时任务名称
        :return:
        """
        try:
            self.scheduler.remove(name)
            return Ok(True)
        except Exception as exc:
            return Err(exc)

    def get(self, name: str) -> Result[Optional[Dict[str, Any]], Exception]:
        """
        获取某个定时任务详情
        :param name: 定时任务名称
        :return:
        """
        try:
            tasks = self.scheduler.list()
            return Ok(tasks.get(name))
        except Exception as exc:
            return Err(exc)

    @staticmethod
    def model(options: Dict[str, Any]) -> Result[Union[crontab | schedule], Exception]:
        """创建定时任务"""
        try:
            schedule_type = options.get('schedule_type', 'crontab')

            if schedule_type == 'crontab':
                # 创建 crontab 调度
                return Ok(crontab(
                    minute=options.get('crontab_minute', '*'),
                    hour=options.get('crontab_hour', '*'),
                    day_of_week=options.get('crontab_day_of_week', '*'),
                    day_of_month=options.get('crontab_day_of_month', '*'),
                    month_of_year=options.get('crontab_month_of_year', '*')
                ))
            elif schedule_type == 'interval':
                # 创建 interval 调度
                seconds = options.get('interval_seconds')
                if seconds is None:
                    return Err(ValueError("interval_seconds 不能为空"))
                return Ok(schedule(run_every=seconds))
            elif schedule_type == 'date' and options.get('run_date'):
                # 一次性任务
                run_date = options['run_date']
                if isinstance(run_date, datetime):
                    # 计算到执行时间的秒数
                    now = datetime.now(run_date.tzinfo)
                    if run_date > now:
                        seconds = (run_date - now).total_seconds()
                        return Ok(schedule(run_every=seconds, relative=True))
                    else:
                        return Err(ValueError("执行时间必须大于当前时间"))
                else:
                    return Err(ValueError("run_date 必须是 datetime 对象"))
            else:
                return Err(ValueError(f"不支持的调度类型: {schedule_type}"))
        except Exception as exc:
            return Err(exc)

    def add(self, options: Dict[str, Any]) -> Result[bool, Exception]:
        """
        添加定时任务
        options: 任务数据字典，包含以下字段：
                - name: 任务名称（唯一）
                - task: 任务完整路径
                - schedule_type: 调度类型
                - crontab_minute/hour/...: crontab 相关字段
                - interval_seconds: interval 相关字段
                - run_date: 一次性任务执行时间
                - args: 位置参数列表
                - kwargs: 关键字参数字典
                - enabled: 是否启用
                - one_off: 是否只执行一次
                - queue/exchange/routing_key/priority: 任务选项
        """
        try:
            # 检查任务名称是否已存在
            existing_tasks = self.scheduler.list()
            if options['name'] in existing_tasks:
                return Err(ValueError(f"任务 '{options['name']}' 已存在"))
            # 创建调度对象
            obj = self.model(options)
            # 准备任务选项
            task_options = {}
            if options.get('queue'):
                task_options['queue'] = options['queue']
            if options.get('exchange'):
                task_options['exchange'] = options['exchange']
            if options.get('routing_key'):
                task_options['routing_key'] = options['routing_key']
            if options.get('priority'):
                task_options['priority'] = options['priority']
            # 添加到调度器
            self.scheduler.add(
                name=options['name'],
                task=options['task'],
                schedule=obj,
                args=options.get('args', []),
                kwargs=options.get('kwargs', {}),
                options=task_options or None,
                enabled=options.get('enabled', True)
            )
            return Ok(True)
        except Exception as exc:
            return Err(exc)

    def update(self, name: str, option: Dict[str, Any]) -> Result[bool, Exception]:
        """更新定时任务"""
        try:
            # 先删除旧任务
            self.remove(name).unwrap()
            option['name'] = name
            return self.add(option)
        except Exception as exc:
            return Err(exc)

    def enable(self, name: str) -> Result[bool, Exception]:
        """启用定时任务"""
        try:
            task = self.get(name).unwrap()
            if task:
                task['enabled'] = True
                return self.update(name, task)
            return Ok(False)
        except Exception as exc:
            return Err(exc)

    def disable(self, name: str) -> Result[bool, Exception]:
        """禁用定时任务"""
        try:
            task = self.get(name).unwrap()
            if task:
                task['enabled'] = False
                return self.update(name, task)
            return Ok(False)
        except Exception as exc:
            return Err(exc)
