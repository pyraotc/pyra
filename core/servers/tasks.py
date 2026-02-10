#!/usr/bin/env python
# -*- coding: utf-8 -*-
def discover_tasks():
    """自动发现并注册定时任务"""
    import importlib
    from conf.settings import INSTALL_APPS, BASE_DIR

    for app_name in INSTALL_APPS:
        app_path = app_name.replace('.', '/')
        tasks_dir = BASE_DIR / app_path / 'tasks'

        if not tasks_dir.exists():
            continue

        task_files = list(tasks_dir.glob('*.py'))
        if not task_files:
            continue

        for task_file in task_files:
            # 跳过__init__.py文件
            if task_file.name == '__init__.py':
                continue

            module_name = f"{app_name}.tasks.{task_file.stem}"
            try:
                # 动态导入模块
                importlib.import_module(module_name)
            except ImportError as e:
                print(f"✗ 导入模块失败: {module_name}, 错误: {str(e)[:100]}...")
            except Exception as e:
                print(f"✗ 处理模块时出错: {module_name}, 错误: {str(e)[:100]}...")
