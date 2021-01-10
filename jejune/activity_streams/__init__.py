import simplejson


from ..serializable import Serializable


AS2_CONTEXT = [
    'https://www.w3.org/ns/activitystreams',
    'https://w3id.org/security/v1',
]


class AS2Object(Serializable):
    def __init__(self, **kwargs):
        kwargs['@context'] = AS2_CONTEXT
        super(AS2Object, self).__init__(**kwargs)

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
        if data['type'] != cls.__name__:
            return None
        return cls(**data)
