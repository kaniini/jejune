
import asyncio
import logging
import simplejson


from . import AS2Object, AS2Pointer, registry
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
        get_jejune_app().rdf_store.override(uri)

        return super().create_if_not_exists(uri, __items__=[])

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

registry.register_type(AS2Collection)


def collection_intersects(collection_uri, item: str) -> bool:
    ptr = AS2Pointer(collection_uri)
    collection = AS2Collection.fetch_local(ptr.serialize(), use_pointers=True)
    if not collection:
        return False

    item_uris = {ptr.serialize() for ptr in collection.__items__}
    return item in item_uris
