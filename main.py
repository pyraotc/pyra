#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sanic_scheduler import SanicScheduler

from core.servers.command import execute_from_command
from core.servers.boot import boot
from core.servers.tasks import discover_tasks

app, host, port, debug, workers = execute_from_command()

scheduler = SanicScheduler()

if __name__ == '__main__':
    if app is not None:
        from core.config import settings

        if settings.get_bool("ENABLED_SCHEDULE"):
            discover_tasks()


        @app.listener('main_process_start')  # 只在主进程执行一次
        async def main_process_start(srv, loop):
            await boot(srv, loop)


        app.run(
            host=host,
            port=port,
            debug=debug,
            workers=workers)
