import aiohttp
import asyncio
import logging
import urllib.parse


from ..http_signatures import HTTPSignatureSigner
from ..activity_streams import AS2Object, AS2Activity, AS2Pointer, AS2_PUBLIC
from ..activity_streams.collection import AS2Collection
from ..activity_pub.actor import Actor


# NOTE: It is planned to process both local *and* remote messages through this
# pipeline, but we're keeping it simple for now.
class InboxProcessorWorker:
    def __init__(self, app):
        self.app = app
        self.queue = []
        self.event = asyncio.Event()

        asyncio.ensure_future(self.work_loop())

    async def process_item(self, item: dict):
        obj = AS2Object.deserialize_from_json(item)

        logging.debug('Processing item %r [%s]', obj.id, obj.serialize())

        if isinstance(obj, AS2Activity):
            await obj.apply_side_effects()

    async def process_queue(self):
        while self.queue:
            await self.process_item(self.queue.pop())

    async def work_loop(self):
        logging.info('Starting inbox processor worker.')

        while True:
            self.event.clear()
            await self.process_queue()
            await self.event.wait()

    def enqueue(self, item: dict):
        self.queue += [item]
        self.event.set()
