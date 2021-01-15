import simplejson


from .. import get_jejune_app
from ..serializable import Serializable


AS2_CONTEXT = [
    'https://www.w3.org/ns/activitystreams',
    'https://w3id.org/security/v1',
    {'jejune': 'https://jejune.dereferenced.org/ns#',
     'storeIdentity': 'jejune:storeIdentity',
     'petName': 'jejune:petName'},
]


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

    def __init__(self, **kwargs):
        header = {'@context': self.__jsonld_context__}
        kwargs['type'] = self.__jsonld_type__

        if 'id' not in kwargs:
            kwargs['id'] = get_jejune_app().rdf_object_uri()

        kwargs['storeIdentity'] = get_jejune_app().rdf_store.hash_for_uri(kwargs['id'])

        if '@context' in kwargs:
            super(AS2Object, self).__init__(**kwargs)
            return

        super(AS2Object, self).__init__(**header, **kwargs)

        self.commit()

    @property
    def jsonld_context(self):
        return getattr(self, '@context')

    @jsonld_context.setter
    def set_jsonld_context(self, context):
        setattr(self, '@context', context)

    @classmethod
    def deserialize(cls, data: str) -> Serializable:
        json_data = simplejson.loads(data)
        return cls.deserialize_from_json(json_data)

    @classmethod
    def deserialize_from_json(cls, data: dict) -> Serializable:
        if data['type'] != cls.__jsonld_type__:
            return None
        return cls(**data)

    @classmethod
    async def fetch_from_uri(cls, uri):
        global registry

        data = await get_jejune_app().rdf_store.fetch_json(uri)
        basetype = registry.type_from_json(data, cls)

        return basetype.deserialize_from_json(data)

    def commit(self):
        get_jejune_app().rdf_store.put_entry(self.id, self.serialize())

    @classmethod
    def create_if_not_exists(cls, uri: str, **kwargs) -> Serializable:
        app = get_jejune_app()
        hashed = app.rdf_store.hash_for_uri(uri)

        if app.rdf_store.hash_exists(hashed):
            data = app.rdf_store.fetch_hash_json(hashed)
            return cls.deserialize_from_json(data)

        return cls(**kwargs, id=uri)

    async def dereference(self) -> Serializable:
        return self


class AS2Pointer:
    def __init__(self, uri: str):
        self.uri = uri

    async def dereference(self) -> Serializable:
        return (await AS2Object.fetch_from_uri(self.uri))