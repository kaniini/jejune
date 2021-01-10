import asyncio
import aiohttp.web
import logging


from . import app


async def start_webserver():
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    listen = app.config['listener'].get('bind', 'localhost')
    port = app.config['listener'].get('port', 8080)

    logging.info('Starting webserver at {listen}:{port}'.format(listen=listen,port=port))

    site = aiohttp.web.TCPSite(runner, listen, port)
    await site.start()


def main():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(start_webserver())
    loop.run_forever()


if __name__ == '__main__':
    main()