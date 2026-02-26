#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import pkgutil

import dotenv
import os
import importlib
from celery import Celery
from celery.signals import celeryd_after_setup

dotenv.load_dotenv()

logger = logging.getLogger(__name__)


def discover_tasks():
    """
    扫描所有应用下的 tasks 目录，自动导入任务模块
    """
    from rcc.config import INSTALL_APPS

    logger.info("开始扫描应用任务...")

    for app_name in INSTALL_APPS:
        try:
            # 导入应用模块
            app_module = importlib.import_module(app_name)

            # 获取应用的物理路径
            app_path = os.path.dirname(app_module.__file__)
            tasks_path = os.path.join(app_path, 'tasks')

            # 检查 tasks 目录是否存在
            if not os.path.exists(tasks_path) or not os.path.isdir(tasks_path):
                logger.debug(f"应用 {app_name} 没有 tasks 目录，跳过")
                continue

            logger.info(f"扫描应用 {app_name} 的 tasks 目录: {tasks_path}")

            # 扫描 tasks 目录下的所有 Python 文件
            tasks_modules = []
            for file in os.listdir(tasks_path):
                if file.endswith('.py') and not file.startswith('__'):
                    module_name = file[:-3]  # 去掉 .py 后缀
                    tasks_modules.append(module_name)

            # 导入每个任务模块
            for module_name in tasks_modules:
                try:
                    full_module_name = f"{app_name}.tasks.{module_name}"
                    module = importlib.import_module(full_module_name)
                    logger.info(f"成功导入任务模块: {full_module_name}")

                    # 可选：列出模块中的所有 Celery 任务
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if callable(attr) and hasattr(attr, '__wrapped__'):  # 简单判断是否为装饰过的函数
                            logger.debug(f"  发现任务函数: {attr_name}")

                except Exception as e:
                    logger.error(f"导入任务模块 {app_name}.tasks.{module_name} 失败: {e}")

        except ImportError as e:
            logger.error(f"导入应用 {app_name} 失败: {e}")
        except Exception as e:
            logger.error(f"扫描应用 {app_name} 任务时发生错误: {e}")

    logger.info("应用任务扫描完成")


# 利用 pkgutil 自动发现
def discover_tasks_simple():
    """
    使用 pkgutil 自动发现所有 tasks 子模块
    """
    from rcc.config import INSTALL_APPS

    logger.info("开始自动发现任务模块...")

    for app_name in INSTALL_APPS:
        try:
            # 构建 tasks 模块的完整名称
            tasks_module_name = f"{app_name}.tasks"

            # 尝试导入 tasks 包
            tasks_package = importlib.import_module(tasks_module_name)

            # 获取 tasks 包的物理路径
            tasks_path = os.path.dirname(tasks_package.__file__)

            # 使用 pkgutil 遍历 tasks 包下的所有模块
            for _, name, ispkg in pkgutil.iter_modules([tasks_path]):
                if not ispkg and not name.startswith('_'):
                    full_module_name = f"{tasks_module_name}.{name}"
                    try:
                        importlib.import_module(full_module_name)
                        logger.info(f"成功导入任务模块: {full_module_name}")
                    except Exception as e:
                        logger.error(f"导入任务模块 {full_module_name} 失败: {e}")

        except ImportError:
            # tasks 模块不存在，跳过
            logger.debug(f"应用 {app_name} 没有 tasks 模块")
            continue
        except Exception as e:
            logger.error(f"处理应用 {app_name} 时发生错误: {e}")


app = Celery(
    'pyra_celery',
    broker=os.environ.get('CELERY_BROKER'),
    backend=os.environ.get('CELERY_BACKEND'),
)

# 引入 RedisBeat 调度器配置
app.conf.update(
    # 使用 RedisBeat 作为 Beat 调度器
    CELERY_BEAT_SCHEDULER='redisbeat.RedisScheduler',
    # 指定 RedisBeat 连接 Redis 的 URL (通常与 Broker 一致)
    CELERY_REDIS_SCHEDULER_URL=os.environ.get('CELERY_BROKER'),
    # 如果想在配置中预设静态定时任务，可以保留 CELERYBEAT_SCHEDULE
    # CELERYBEAT_SCHEDULE = {...}

    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=20 * 60,
)


# 在 Celery 启动时执行任务发现
@celeryd_after_setup.connect
def capture_worker_tasks(sender, instance, **kwargs):
    discover_tasks_simple()


discover_tasks_simple()
