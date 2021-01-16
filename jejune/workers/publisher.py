import asyncio
import logging


from ..activity_streams import AS2Activity


class PublisherRequest:
    def __init__(self, activity: AS2Activity, recipient: str):
        self.activity = activity
        self.error_count = 0
        self.complete = False

    async def publish(self):
        return self.error()

    def error(self):
        self.error_count += 1
        return self

    def maybe_cull(self):
        if self.error_count > 10:
            logging.info('Culling publish request for activity %s to %s due to excessive errors (%d).',
                         self.activity.id, self.recipient, self.error_count)
            return True

        return self.complete


class PublisherWorker:
    def __init__(self, app):
        self.app = app
        self.queue = []
        self.event = asyncio.Event()

        asyncio.ensure_future(self.work_loop())
        asyncio.ensure_future(self.wakeup_loop())

    def add_activity(self, activity: AS2Activity, recipient: str) -> PublisherRequest:
        pr = PublisherRequest(activity, recipient)
        self.queue += [pr]
        self.event.set()
        return pr

    def cull_queue(self):
        self.queue = [pr for pr in self.queue if not pr.maybe_cull()]

    async def process_requests(self):
        logging.info('Publisher work queue has %d items.', len(self.queue))

        if len(self.queue) == 0:
            return

        await asyncio.wait([pr.publish() for pr in self.queue])

    async def work_loop(self):
        logging.info('Starting publisher worker.')

        while True:
            self.event.clear()
            await self.process_requests()
            await self.event.wait()

    async def wakeup_loop(self):
        sleep_time = 10

        logging.info('Publisher worker will sleep for a maximum of %d seconds.', sleep_time)

        while True:
            await asyncio.sleep(sleep_time)
            self.event.set()