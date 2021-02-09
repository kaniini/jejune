import aiohttp
import asyncio
import base64
import hashlib
import logging
import time
import urllib.parse


from ..http_signatures import HTTPSignatureSigner
from ..activity_streams import AS2Object, AS2Activity, AS2Pointer, AS2_PUBLIC
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
        self.originator = AS2Pointer(self.activity.actor).dereference()

    async def handle_local_delivery(self):
        obj = AS2Collection.fetch_local(self.recipient, use_pointers=True)

        if isinstance(obj, AS2Collection) and not obj.contains_uri(self.activity.id):
            obj.prepend(self.activity)
            obj.commit()

            asyncio.ensure_future(self.publisher.notify_listeners(obj.id, self.activity))

        return self.completed()

    def handle_public(self):
        if self.activity.__ephemeral__:
            return self.completed()

        self.publisher.add_activity(self.activity, self.publisher.app.shared_inbox_uri, LOCAL_DELIVERY)
        return self.completed()

    def handle_actor(self, actor: Actor):
        if actor.local() and not self.activity.__ephemeral__:
            self.publisher.add_activity(self.activity, actor.inbox, LOCAL_DELIVERY)
            return self.completed()

        self.publisher.add_activity(self.activity, actor.inbox, AP_INBOX)
        return self.completed()

    def handle_collection(self, obj: AS2Collection):
        if not self.activity.__ephemeral__:
            local = [self.publisher.add_activity(self.activity, actor.inbox, LOCAL_DELIVERY)
                     for actor in obj.__items__ if isinstance(actor, Actor) and actor.local()]

        inboxes = set([actor.best_inbox() for actor in obj.__items__ if isinstance(actor, Actor) and actor.remote()])
        logging.info('PUBLISHER: Expanded collection %r to %r.', obj.id, inboxes)
        [self.publisher.add_activity(self.activity, inbox, AP_INBOX) for inbox in inboxes]
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
        # We can't deliver on behalf of remote users.
        if not self.originator.local():
            logging.info('PUBLISHER: WTF: Trying to deliver messages on behalf of remote user %s.', self.originator.id)
            return self.completed()

        user = self.originator.user()

        payload = self.activity.serialize()
        uri = urllib.parse.urlsplit(self.recipient)
        digest = base64.b64encode(hashlib.sha256(payload.encode('utf-8')).digest()).decode('utf-8')

        headers = {
            '(request-target)': 'post %s' % uri.path,
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/activity+json',
            'User-Agent': self.publisher.app.user_agent,
            'Host': uri.netloc,
            'Digest': 'SHA-256=' + digest,
            'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()),
        }

        privkey = user.privkey()

        headers['signature'] = self.publisher.signer.sign(headers, privkey, actor.publicKey['id'])
        headers.pop('(request-target)')
        headers.pop('Host')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.recipient, data=payload, headers=headers) as resp:
                    if resp.status == 202:
                        return self.completed()
                    elif resp.status >= 500:
                        return self.error()

                    resp_payload = await resp.text()
                    logging.debug('%r >> %r', self.recipient, resp_payload)
                    return self.completed()
        except Exception as e:
            logging.info('Exception %r when pushing to %s.', e, self.recipient)
            return self.error()

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
        self.signer = HTTPSignatureSigner()
        self.listeners = {}

        asyncio.ensure_future(self.work_loop())
        asyncio.ensure_future(self.wakeup_loop())

    def add_activity(self, activity: AS2Activity, recipient: str, kind=AS2_RECIPIENT) -> PublisherRequest:
        logging.debug('Enqueueing activity %s for publishing to recipient %r (kind %d).', activity.id, recipient, kind)

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

    def listeners_for_uri(self, uri: str) -> list:
        return self.listeners.get(uri, [])

    def attach_uri_listener(self, uri: str, listener):
        listeners = self.listeners_for_uri(uri)
        self.listeners[uri] = listeners + [listener]

    async def notify_listeners(self, uri: str, activity):
        tasks = [listener(uri, activity) for listener in self.listeners_for_uri(uri)]
        if tasks:
            await asyncio.wait(tasks, timeout=5)
