from .serializable import Serializable


class Collection(Serializable):
    @classmethod
    def new(cls):
        return cls(items=[])

    def append(self, item):
        self.items += [item]

    def prepend(self, item):
        self.items = [item] + self.items

    def remove(self, item):
        self.items.remove(item)
