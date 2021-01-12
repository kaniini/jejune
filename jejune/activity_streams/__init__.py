import simplejson


from ..serializable import Serializable


AS2_CONTEXT = [
    'https://www.w3.org/ns/activitystreams',
    'https://w3id.org/security/v1',
    {'jejune': 'https://jejune.dereferenced.org/ns#',
     'graphIdentity': 'jejune:graphIdentity',
     'petName': 'jejune:petName'},
]


class AS2Object(Serializable):
    __jsonld_context__ = AS2_CONTEXT
    __jsonld_type__ = 'Object'

    def __init__(self, **kwargs):
        header = {'@context': self.__jsonld_context__}
        kwargs['type'] = self.__jsonld_type__

        if '@context' in kwargs:
            super(AS2Object, self).__init__(**kwargs)
            return

        super(AS2Object, self).__init__(**header, **kwargs)

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
