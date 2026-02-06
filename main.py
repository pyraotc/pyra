#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.servers.command import execute_from_command

app, host, port, debug, workers = execute_from_command()

if __name__ == '__main__':
    if app is not None:
        @app.listener('main_process_start')  # 只在主进程执行一次
        async def main_process_start(srv, loop):
            pass


        app.run(
            host=host,
            port=port,
            debug=debug,
            workers=workers)
