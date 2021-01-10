from . import logging


import asyncio
import aiohttp
import aiohttp.web
import os


from . import application_factory


if 'JEJUNE_CONFIG' not in os.environ:
    print('JEJUNE_CONFIG is not in environment, cannot load application')
    exit()


app = application_factory.Application(os.environ['JEJUNE_CONFIG'])