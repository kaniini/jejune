import asyncio
import logging


from ..activity_streams import AS2Object, AS2Activity, AS2_PUBLIC
from ..activity_streams.collection import AS2Collection
from ..activity_pub.actor import Actor


AS2_RECIPIENT = 1
AP_INBOX = 2
LOCAL_DELIVERY = 3


class PublisherRequest:
    def __init__(self, publisher, activity: AS2Activity, recipient: str, kind=AS2_RECIPIENT):
        self.publisher = publisher
        self.activity = activity
        self.recipient = recipient
        self.kind = kind
        self.error_count = 0
        self.complete = False

    async def handle_local_delivery(self):
        obj = await AS2Object.fetch_from_uri(self.recipient)

        obj.prepend(self.activity)
        obj.commit()

        return self.completed()

    def handle_public(self):
        self.publisher.add_activity(self.activity, self.publisher.app.shared_inbox_uri, LOCAL_DELIVERY)
        return self.completed()

    def handle_actor(self, actor: Actor):
        if actor.local():
            self.publisher.add_activity(self.activity, actor.inbox, LOCAL_DELIVERY)
            return

        self.publisher.add_activity(self.activity, actor.inbox, AP_INBOX)
        return self.completed()

    def handle_collection(self, obj: AS2Collection):
        local = [self.publisher.add_activity(self.activity, actor.inbox, LOCAL_DELIVERY)
                 for actor in obj.__items__ if isinstance(obj, Actor) and obj.local()]

        inboxes = [actor.best_inbox() for actor in obj.__items__ if isinstance(obj, Actor) and obj.remote()]
        [self.publisher.add_activity(self.activity, inbox, AP_INBOX) for inbox in set(inboxes)]
        return self.completed()

    async def handle_as2_recipient(self):
        if self.recipient == AS2_PUBLIC:
            return self.handle_public()

        obj = await AS2Object.fetch_from_uri(self.recipient)
        if isinstance(obj, AS2Collection):
            return self.handle_collection(obj)
        elif isinstance(obj, Actor):
            return self.handle_actor(obj)

        return self.fatality()

    async def handle_ap_inbox(self):
        logging.error('Delivering to remote AP inboxes is not implemented yet.')
        return self.fatality()

    async def publish(self):
        logging.info('Publishing %s to %s (type %d).', self.activity.id, self.recipient, self.kind)

        if self.kind == AS2_RECIPIENT:
            return (await self.handle_as2_recipient())
        elif self.kind == AP_INBOX:
            return (await self.handle_ap_inbox())
        elif self.kind == LOCAL_DELIVERY:
            return (await self.handle_local_delivery())

        logging.error('Not sure how to handle publish request type %d.', self.kind)
        return self.fatality()

    def completed(self):
        self.complete = True
        return self

    def fatality(self):
        self.error_count = 9999999
        return self

    def error(self):
        self.error_count += 1
        return self

    def maybe_cull(self):
        if self.error_count > 3:
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

    def add_activity(self, activity: AS2Activity, recipient: str, kind=AS2_RECIPIENT) -> PublisherRequest:
        pr = PublisherRequest(self, activity, recipient, kind)
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
            self.cull_queue()
            await self.event.wait()

    async def wakeup_loop(self):
        sleep_time = 10

        logging.info('Publisher worker will sleep for a maximum of %d seconds.', sleep_time)

        while True:
            await asyncio.sleep(sleep_time)
            self.event.set()