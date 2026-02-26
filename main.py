from sanic_scheduler import SanicScheduler

from server.command import execute_from_command, load_data

app, host, port, debug, workers = execute_from_command()

scheduler = SanicScheduler()

if __name__ == '__main__':
    if app is not None:
        @app.listener('main_process_start')  # 只在主进程执行一次
        async def main_process_start(srv, loop):
            await load_data(srv, loop)


        app.run(
            host=host,
            port=port,
            debug=debug,
            workers=workers)
