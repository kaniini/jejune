__version__ = '0.0.1'


from . import logging


import asyncio
import aiohttp
import aiohttp.web
import os


app = None
JEJUNE_APP = None

def get_jejune_app():
    global JEJUNE_APP
    return JEJUNE_APP


from . import application_factory


if 'JEJUNE_CONFIG' not in os.environ:
    print('JEJUNE_CONFIG is not in environment, cannot load application')
    exit()


app = JEJUNE_APP = application_factory.Application(os.environ['JEJUNE_CONFIG'])


from . import web