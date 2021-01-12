import simplejson


from .serializable import Serializable


class Collection(Serializable):
    def __repr__(self):
        return '<{0}: {1} items>'.format(type(self).__name__, len(self.items))

    @classmethod
    def new(cls):
        return cls(items=[])

    def append(self, item):
        self.items += [item]

    def prepend(self, item):
        self.items = [item] + self.items

    def remove(self, item):
        self.items.remove(item)


class TypedCollection(Collection):
    __child_type__ = Serializable
    __item_key__ = 'items'

    def serialize(self, method=simplejson.dumps):
        data = {self.__item_key__: [child.serialize(dict) for child in self.items]}
        return method(data)

    @classmethod
    def deserialize(cls, json_data: str) -> Collection:
        data = simplejson.loads(json_data)
        return cls(items=[cls.__child_type__(**obj) for obj in data[cls.__item_key__]])
