import asyncio
import logging
import simplejson
import time
import traceback
import urllib.parse


from .. import get_jejune_app
from ..serializable import Serializable


from cachetools import TTLCache



AS2_PUBLIC = 'https://www.w3.org/ns/activitystreams#Public'
AS2_CONTEXT = [
    'https://www.w3.org/ns/activitystreams',
    'https://w3id.org/security/v1',
    {'jejune': 'https://jejune.dereferenced.org/ns#',
     'storeIdentity': 'jejune:storeIdentity',
     'petName': 'jejune:petName',
     'submittedBy': 'jejune:submittedBy',
     'litepub': 'http://litepub.social/ns#',
     'oauthRegistrationEndpoint': {
          '@type': '@id',
          '@id': 'litepub:oauthRegistrationEndpoint'
     },
     'sharedOutbox': {
          '@type': '@id',
          '@id': 'jejune:sharedOutbox'
     },
     'searchEndpoint': {
          '@type': '@id',
          '@id': 'jejune:searchEndpoint'
     },
     'shared': {
          '@type': '@id',
          '@id': 'jejune:shared'
     },
     'interactionCount': 'jejune:interactionCount',
     'objectSerial': 'jejune:objectSerial'}
]
SERIAL_CACHE = TTLCache(500, 300)
AS2_OBJECT_CACHE = TTLCache(16384, 3600)


class AS2TypeRegistry:
    __types__ = {}

    def register(self, typename: str, klass: type):
        self.__types__[typename] = klass

    def register_type(self, klass: type):
        self.register(klass.__jsonld_type__, klass)

    def type_from_json(self, data: dict, default=None) -> type:
        return self.__types__.get(data.get('type', 'Object'), default)

registry = AS2TypeRegistry()


class AS2Object(Serializable):
    __jsonld_context__ = AS2_CONTEXT
    __jsonld_type__ = 'Object'
    __ephemeral__ = False
    __interactive__ = True

    def __init__(self, **kwargs):
        header = {'@context': self.__jsonld_context__}
        if 'type' not in kwargs:
            kwargs['type'] = self.__jsonld_type__

        if 'id' not in kwargs:
            kwargs['id'] = get_jejune_app().rdf_object_uri()

        if 'published' not in kwargs:
            kwargs['published'] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # ensure we are fetching any relevant actors ahead of time
        if kwargs.get('attributedTo', None):
            AS2Pointer(kwargs['attributedTo']).dereference()

        if 'actor' in kwargs:
            AS2Pointer(kwargs['actor']).dereference()

        # fail closed rather than open
        if 'audience' not in kwargs:
            to = kwargs.get('to', [])
            cc = kwargs.get('cc', [])

            if not isinstance(to, list):
                to = [to]

            if not isinstance(cc, list):
                cc = [cc]

            kwargs['audience'] = to + cc

        kwargs['storeIdentity'] = get_jejune_app().rdf_store.hash_for_uri(kwargs['id'])

        if 'actor' not in kwargs and 'attributedTo' not in kwargs and 'submittedBy' in kwargs:
            kwargs['attributedTo'] = kwargs['submittedBy']

        if 'objectSerial' not in kwargs:
            kwargs['objectSerial'] = 0

        if self.__interactive__:
            kwargs['replies'] = self.create_collection(kwargs.get('replies', None))
            kwargs['likes'] = self.create_collection(kwargs.get('likes', None))
            kwargs['shares'] = self.create_collection(kwargs.get('shares', None))
            kwargs['interactionCount'] = kwargs.get('interactionCount', 0)

        asyncio.ensure_future(self.synchronize())

        if '@context' in kwargs:
            super(AS2Object, self).__init__(**kwargs)

            if self.local():
                self.update_context()

            self.commit()
            return

        super(AS2Object, self).__init__(**header, **kwargs)

        self.commit()

    def create_collection(self, uri=None):
        from .collection import AS2Collection

        app = get_jejune_app()
        if not uri:
            uri = app.object_uri('collection')

        ptr = AS2Pointer(uri)
        AS2Collection.create_if_not_exists(ptr.id)
        app.rdf_store.override(ptr.id)

        return ptr.id

    @property
    def jsonld_context(self):
        return getattr(self, '@context')

    @jsonld_context.setter
    def set_jsonld_context(self, context):
        setattr(self, '@context', context)

    def update_context(self):
        setattr(self, '@context', AS2_CONTEXT)

    @classmethod
    def deserialize(cls, data: str) -> Serializable:
        json_data = simplejson.loads(data)
        return cls.deserialize_from_json(json_data)

    @classmethod
    def deserialize_from_json(cls, data: dict) -> Serializable:
        if 'id' in data and data['id'] in AS2_OBJECT_CACHE:
            return AS2_OBJECT_CACHE[data['id']]

        global registry

        if data['type'] != cls.__jsonld_type__:
            basetype = registry.type_from_json(data, None)

            if not basetype:
                return cls(**data)

            return basetype.deserialize_from_json(data)

        return cls(**data)

    @classmethod
    async def fetch_from_uri(cls, uri):
        if uri in AS2_OBJECT_CACHE:
            return AS2_OBJECT_CACHE[uri]

        data = await get_jejune_app().rdf_store.fetch_json(uri)
        if not data:
            return None

        return cls.deserialize_from_json(data)

    @classmethod
    def fetch_cached_from_uri(cls, uri):
        if uri in AS2_OBJECT_CACHE:
            return AS2_OBJECT_CACHE[uri]

        app = get_jejune_app()
        hashed = app.rdf_store.hash_for_uri(uri)

        return cls.fetch_from_hash(hashed)

    @classmethod
    def fetch_from_hash(cls, hashed):
        if hashed in AS2_OBJECT_CACHE:
            return AS2_OBJECT_CACHE[hashed]

        app = get_jejune_app()

        data = app.rdf_store.fetch_hash_json(hashed)
        if not data:
            return None

        return cls.deserialize_from_json(data)

    def update_url(self):
        if not getattr(self, 'url', None):
            self.url = get_jejune_app().frontend_support.friendly_uri(self)

    def commit(self):
        if self.objectSerial < SERIAL_CACHE.get(self.id, 0):
            logging.info('WTF: Serial for %r went backwards (%d < %d).', self.id, self.objectSerial, SERIAL_CACHE.get(self.id, 0))
            traceback.print_stack()
            return

        self.objectSerial += 1
        self.update_url()

        # logging.debug('RDF: Committing %r.', self.id)
        get_jejune_app().rdf_store.put_entry(self.id, self.serialize())
        SERIAL_CACHE[self.id] = self.objectSerial
        AS2_OBJECT_CACHE[self.id] = self
        AS2_OBJECT_CACHE[self.storeIdentity] = self

    @classmethod
    def create_if_not_exists(cls, uri: str, **kwargs) -> Serializable:
        if uri in AS2_OBJECT_CACHE:
            return AS2_OBJECT_CACHE[uri]

        app = get_jejune_app()

        hashed = app.rdf_store.hash_for_uri(uri)

        if app.rdf_store.hash_exists(hashed):
            data = app.rdf_store.fetch_hash_json(hashed)

            if data:
                return cls.deserialize_from_json(data)

        return cls(**kwargs, id=uri)

    async def dereference(self) -> Serializable:
        return self

    def local(self):
        return get_jejune_app().rdf_store.uri_is_local(self.id)

    def remote(self):
        return not self.local()

    def serialize_to_mastodon(self):
        return {'error': 'serialization to mastodon format is not supported for this type',
                'type': self.__jsonld_type__,
                'asid': self.id}

    def mastodon_id(self):
        return self.storeIdentity

    def published_ts(self):
        if not self.published:
            return 0.0

        try:
            st = time.strptime(self.published, '%Y-%m-%dT%H:%M:%SZ')
            return time.mktime(st)
        except ValueError:
            try:
                st = time.strptime(self.published, '%Y-%m-%dT%H:%M:%S.%fZ')
                return time.mktime(st)
            except ValueError:
                pass

        return 0.0

    def published_time(self):
        return time.strftime('%B %d, %Y [%H:%M:%S]', time.localtime(self.published_ts()))

    def gather_interaction_stream(self, stream: str) -> list:
        from .collection import AS2Collection

        if not self.__interactive__:
            return []

        stream_uri = getattr(self, stream, None)
        if not stream_uri:
            return []

        collection = AS2Collection.fetch_local(stream_uri, use_pointers=True)
        return collection.__items__

    def gather_interactions(self):
        if not self.__interactive__:
            return []

        replies = self.gather_interaction_stream('replies')
        likes = self.gather_interaction_stream('likes')
        shares = self.gather_interaction_stream('shares')

        merged = [item.dereference() for item in replies + likes + shares]
        merged = [item for item in merged if item]

        self.interactionCount = len(merged)
        self.commit()

        return sorted(merged, key=lambda x: x.published_ts(), reverse=True)

    def update_interaction_count(self):
        self.gather_interactions()

    def visible_for(self, actor=None) -> bool:
        attribution = getattr(self, 'attributedTo', getattr(self, 'actor', None))
        audience = getattr(self, 'audience', [attribution])

        if AS2_PUBLIC in audience:
            return True

        if actor:
            return actor.id in audience

        return False

    async def announce_update(self):
        pass

    async def synchronize(self):
        pass

    def reply(self):
        if getattr(self, 'inReplyTo', None):
            return AS2Pointer(self.inReplyTo).dereference()

        return None

    def attributed_object(self):
        attribution = getattr(self, 'attributedTo', getattr(self, 'actor', None))
        if not attribution:
            return None

        return AS2Pointer(attribution).dereference()

    def attachments(self):
        return getattr(self, 'attachment', [])

    def domain(self):
        return urllib.parse.urlparse(self.id).netloc

registry.register_type(AS2Object)


DEREF_DEPTH = 0


class AS2Pointer:
    def __init__(self, uri):
        if isinstance(uri, str):
            self.id = uri
        elif isinstance(uri, dict):
            try:
                obj = AS2Object.deserialize_from_json(uri)
                if obj:
                    self.id = obj.id
                else:
                    self.id = uri['id']
            except:
                self.id = uri['id']
        elif isinstance(uri, AS2Object):
            self.id = uri.id
        else:
            logging.exception('AS2Pointer: Cannot construct a pointer for %r.', uri)

    def __repr__(self):
        return f'<AS2Pointer: {self.id}>'

    def dereference(self) -> AS2Object:
        global DEREF_DEPTH

        DEREF_DEPTH += 1

        if DEREF_DEPTH > 50:
            logging.info('WTF: Loop (or unusually complex JSON-LD graph) detected, ptr=%r.', self.id)
            return None

        obj = AS2Object.fetch_cached_from_uri(self.id)
        if not obj:
            asyncio.ensure_future(self.load())

        DEREF_DEPTH -= 1

        return obj

    @classmethod
    def pointerize(cls, obj: AS2Object):
        return cls(obj.id)

    def serialize(self):
        return self.id

    async def load(self, payload=None) -> AS2Object:
        if not payload:
            return await (AS2Object.fetch_from_uri(self.id))

        if isinstance(payload, dict):
            return AS2Object.deserialize_from_json(payload)

        assert isinstance(payload, str)
        return (await AS2Object.fetch_from_uri(payload))


class AS2Activity(AS2Object):
    __jsonld_type__ = 'Activity'
    __interactive__ = False

    def __init__(self, **kwargs):
        if 'actor' not in kwargs and 'attributedTo' not in kwargs and 'submittedBy' in kwargs:
            kwargs['actor'] = kwargs['submittedBy']

        if 'object' in kwargs and type(kwargs['object']) != str:
            child_obj = kwargs.pop('object')

            child_ptr = AS2Pointer(child_obj)
            kwargs['object'] = child_ptr.serialize()

            if not child_ptr.dereference():
                asyncio.ensure_future(child_ptr.load(payload=child_obj))

        super().__init__(**kwargs)

    def child(self) -> AS2Object:
        if not self.object:
            return None

        child = AS2Pointer(self.object).dereference()
        if not child:
            asyncio.ensure_future(AS2Pointer(self.object).load())

        return child

    def update_interaction_count(self):
        child = self.child()
        if child:
            child.update_interaction_count()

    async def publish(self):
        app = get_jejune_app()

        # splice into outbox
        actor = await AS2Object.fetch_from_uri(self.actor or self.attributedTo)
        if actor:
            app.publisher.add_activity(self, actor.outbox, 3)

        # splice into shared outbox
        if self.local():
            app.publisher.add_activity(self, get_jejune_app().shared_outbox_uri, 3)

        # enqueue sends to recipients
        [app.publisher.add_activity(self, recipient) for recipient in self.get_audience()]

    def address_list(self, attrlist: str) -> list:
        addresses = getattr(self, attrlist, [])

        if type(addresses) != list:
            addresses = [addresses]

        return addresses

    def get_audience(self):
        return self.address_list('to') + self.address_list('cc')

    def fix_child_audience(self):
        child = self.child()

        if not child or child.audience:
            return

        child.audience = self.get_audience()
        child.commit()

    async def apply_side_effects(self):
        self.fix_child_audience()
        await self.publish()

    async def accept_side_effects(self, parent):
        pass

    async def reject_side_effects(self, parent):
        pass

    def serialize_to_mastodon(self):
        child = self.child()

        if child:
            return child.serialize_to_mastodon()

        return super().serialize_to_mastodon()

    def serialize(self, method=simplejson.dumps):
        base = super().serialize(dict)

        child = self.child()
        if child:
            base['object'] = child.serialize(dict)

        return method(base)

registry.register_type(AS2Activity)
