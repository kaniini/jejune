import asyncio
import logging
import simplejson


from . import AS2_CONTEXT, AS2Object, AS2Pointer, registry
from ..collection import TypedCollection


def handle_pointer(cls, obj):
    if type(obj) == dict:
        return cls.__child_type__.deserialize_from_json(obj)
    elif type(obj) == str:
        return AS2Pointer(obj).dereference()


def handle_flat_pointer(obj):
    if type(obj) == dict:
        return AS2Pointer(obj['id'])
    else:
        return AS2Pointer(obj)


class AS2Collection(AS2Object, TypedCollection):
    __jsonld_type__ = 'Collection'
    __child_type__ = AS2Object
    __interactive__ = False

    def walk(self, object_types: set, limit: int, skip=0, max_id=None, since_id=None, min_id=None, visible_for=None) -> list:
        yielded = 0
        skipped = 0
        max_hit = max_id is None

        for obj in self.__items__:
            real = obj.dereference()
            if not real:
                continue

            if object_types and real.type not in object_types:
                continue

            if skip and skipped < skip:
                skipped += 1
                continue

            if limit and yielded > limit:
                break

            item_id = real.mastodon_id()
            if max_id and item_id == max_id:
                max_hit = True

            if not max_hit:
                continue

            if not real.visible_for(visible_for):
                continue

            if since_id and item_id == since_id:
                break

            yielded += 1
            yield real

            if min_id and item_id == min_id:
                break

    def serialize(self, method=simplejson.dumps, flatten_pointers=True):
        if not flatten_pointers:
            return super().serialize(method)

        obj = {k: v for k, v in self.__dict__.items() if not k.startswith('__')}
        obj[self.__item_key__] = [obj.id for obj in self.__items__ if obj]

        return method(obj)

    @classmethod
    def deserialize_from_json(cls, data: dict, use_pointers=False) -> AS2Object:
        if data['type'] != cls.__jsonld_type__:
            return None

        items = data.pop(cls.__item_key__)
        if not use_pointers:
            return cls(**data, __items__=[handle_pointer(cls, obj) for obj in items])
        else:
            return cls(**data, __items__=[handle_flat_pointer(obj) for obj in items])

    @classmethod
    def create_if_not_exists(cls, uri: str, **kwargs) -> AS2Object:
        from . import get_jejune_app

        app = get_jejune_app()
        app.rdf_store.override(uri)

        hashed = app.rdf_store.hash_for_uri(uri)

        if app.rdf_store.hash_exists(hashed):
            data = app.rdf_store.fetch_hash_json(hashed)

            if data:
                return cls.deserialize_from_json(data, use_pointers=True)

        return cls(**kwargs, id=uri, __items__=[])

    @classmethod
    def fetch_local(cls, uri: str, use_pointers=True) -> AS2Object:
        from . import get_jejune_app

        app = get_jejune_app()
        hashed = app.rdf_store.hash_for_uri(uri)
        data = get_jejune_app().rdf_store.fetch_hash_json(hashed)
        if not data:
            return None

        return cls.deserialize_from_json(data, use_pointers=use_pointers)

    @classmethod
    async def fetch_from_uri(cls, uri: str, use_pointers=True) -> AS2Object:
        from . import get_jejune_app

        app = get_jejune_app()
        data = await get_jejune_app().rdf_store.fetch_json(uri)
        if not data:
            return None

        return cls.deserialize_from_json(data, use_pointers=use_pointers)

    def contains_uri(self, uri: str) -> bool:
        uris = {item.id for item in self.__items__}
        return uri in uris

registry.register_type(AS2Collection)


def collection_intersects(collection_uri, item: str) -> bool:
    ptr = AS2Pointer(collection_uri)
    collection = AS2Collection.fetch_local(ptr.serialize(), use_pointers=True)
    if not collection:
        return False

    item_uris = {ptr.serialize() for ptr in collection.__items__}
    return item in item_uris


class OrderedCollectionAdapter:
    def __init__(self, coll: AS2Collection):
        self.coll = coll

    def serialize(self, request):
        items_per_page = 20
        last_page = int(len(self.coll) / items_per_page)

        actor = None
        user = request.get('oauth_user', None)
        if user:
            actor = user.actor()

        if 'page' not in request.query:
            return {
                '@context': AS2_CONTEXT,
                'id': self.coll.id,
                'type': 'OrderedCollection',
                'totalItems': len(self.coll),
                'first': self.coll.id + '?page=0',
                'last': self.coll.id + f'?page={last_page}'
            }

        page = int(request.query.get('page', 0))
        skip = items_per_page * page
        items = self.coll.walk({}, items_per_page, skip=skip, visible_for=actor)
        result = {
            '@context': AS2_CONTEXT,
            'id': self.coll.id + f'?page={page}',
            'type': 'OrderedCollectionPage',
            'partOf': self.coll.id,
            'orderedItems': [item.serialize(dict) for item in items],
        }

        if page:
            result['prev'] = self.coll.id + f'?page={page - 1}'

            if page < last_page:
                result['next'] = self.coll.id + f'?page={page + 1}'

        return result
