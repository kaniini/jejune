from jejune.serializable import Serializable
from jejune.collection import Collection, TypedCollection


class Foo(Serializable):
    pass


class FooCollection(TypedCollection):
    __child_type__ = Foo


def test_basic_collection():
    children = [1, 2, 3]

    c = Collection.new(children)
    assert c.serialize() == '{"items": [1, 2, 3]}'

    c2 = Collection.deserialize(c.serialize())
    assert c2.__items__ == c.__items__


def test_typed_collection():
    f1 = Foo(name='a')
    f2 = Foo(name='b')

    fc = FooCollection.new([f1, f2])
    assert fc.serialize() == '{"items": [{"name": "a"}, {"name": "b"}]}'

    fc2 = FooCollection.deserialize(fc.serialize())
    assert fc.serialize() == fc2.serialize()
