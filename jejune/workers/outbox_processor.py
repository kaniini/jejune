import asyncio
import logging


# This does some preprocessing on C2S activities before handing them off to 
# InboxProcessorWorker.
class OutboxProcessorWorker:
    def __init__(self, app):
        self.app = app
        self.queue = []
        self.event = asyncio.Event()

        asyncio.ensure_future(self.work_loop())

    def enqueue(self, item: dict, actor: str):
        item['submittedBy'] = actor
        self.queue += [item]
        self.event.set()

    async def process_item(self, item: dict):
        mentions = []
        child = item.get('object', item)

        if isinstance(child, dict) and 'source' in child.keys():
            source = child['source']

            if isinstance(source, str):
                source = {'content': source}

            content = source['content']
            content, mentions = await self.app.formatter.format(content, source.get('mediaType', 'text/markdown'))
            child['content'] = content

            tags = [{'href': actor.id, 'name': f'@{actor.petName}', 'type': 'Mention'} for actor in mentions]
            child['tag'] = child.get('tag', []) + tags

            if child != item:
                item['object'] = child

        self.app.inbox_processor.enqueue(item)

    async def process_queue(self):
        while self.queue:
            await self.process_item(self.queue.pop())

    async def work_loop(self):
        logging.info('Starting outbox processor worker.')

        while True:
            self.event.clear()
            await self.process_queue()
            await self.event.wait()
