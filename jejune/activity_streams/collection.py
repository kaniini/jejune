from . import AS2Object
from ..collection import TypedCollection


class AS2Collection(AS2Object, TypedCollection):
    __jsonld_type__ = 'Collection'

    @classmethod
    def deserialize_from_json(cls, data: dict) -> AS2Object:
        if data['type'] != cls.__jsonld_type__:
            return None

        items = data.pop(cls.__item_key__)
        return cls(**data, __items__=[cls.__child_type__.deserialize_from_json(obj) for obj in items])

    @classmethod
    def create_if_not_exists(cls, uri: str, **kwargs) -> AS2Object:
        return super().create_if_not_exists(uri, __items__=[])