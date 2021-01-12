import simplejson


from .serializable import Serializable


class Collection(Serializable):
    __item_key__ = 'items'
    __items__ = []

    def __repr__(self):
        return '<{0}: {1} items>'.format(type(self).__name__, len(self.__items__))

    @classmethod
    def new(cls, items=[]):
        return cls(__items__=items)

    def append(self, item):
        self.__items__ += [item]

    def prepend(self, item):
        self.__items__ = [item] + self.__items__

    def remove(self, item):
        self.__items__.remove(item)

    def serialize(self, method=simplejson.dumps):
        return method({self.__item_key__: self.__items__})

    @classmethod
    def deserialize(cls, json_data: str) -> Serializable:
        data = simplejson.loads(json_data)
        return cls(__items__=data[cls.__item_key__])


class TypedCollection(Collection):
    __child_type__ = Serializable

    def serialize(self, method=simplejson.dumps):
        data = super(Collection, self).serialize(dict)
        data[self.__item_key__] = [child.serialize(dict) for child in self.__items__]
        return method(data)

    @classmethod
    def deserialize(cls, json_data: str) -> Collection:
        data = simplejson.loads(json_data)
        items = [cls.__child_type__(**obj) for obj in data[cls.__item_key__]]

        del data[cls.__item_key__]
        data['__items__'] = items

        return cls(**data)
