__version__ = '0.0.1'


from . import logging


import asyncio
import aiohttp
import aiohttp.web
import os


app = None

def get_jejune_app():
    global app
    return app


from . import application_factory


if 'JEJUNE_CONFIG' not in os.environ:
    print('JEJUNE_CONFIG is not in environment, cannot load application')
    exit()


app = application_factory.Application(os.environ['JEJUNE_CONFIG'])


from . import web