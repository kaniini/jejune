import asyncio


from . import AS2Object, AS2Pointer
from ..collection import TypedCollection


def handle_pointer(cls, obj):
    if type(obj) == dict:
        return cls.__child_type__.deserialize_from_json(obj)
    else if type(obj) == str:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(AS2Pointer(obj).dereference())


class AS2Collection(AS2Object, TypedCollection):
    __jsonld_type__ = 'Collection'

    def serialize(self, method=simplejson.dumps, flatten_pointers=False):
        if not flatten_pointers:
            return super().serialize(method)

        obj = {k: v for k, v in self.__dict__.items()}
        obj[self.__item_key__] = [obj.id for obj in self.__items__]
        return method(obj)

    @classmethod
    def deserialize_from_json(cls, data: dict) -> AS2Object:
        if data['type'] != cls.__jsonld_type__:
            return None

        items = data.pop(cls.__item_key__)
        return cls(**data, __items__=[handle_pointer(cls, obj) for obj in items])

    @classmethod
    def create_if_not_exists(cls, uri: str, **kwargs) -> AS2Object:
        return super().create_if_not_exists(uri, __items__=[])