import simplejson


class Serializable:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "<{0} ({1} properties)>".format(type(self).__name__, len(self.__dict__))

    @classmethod
    def deserialize(cls, data: str):
        properties = simplejson.loads(data)
        return cls(**properties)

    def serialize(self, method=simplejson.dumps):
        values = {k: v for k, v in self.__dict__.items() if not k.startswith('__')}
        return method(values)