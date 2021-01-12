from jejune.activity_streams import AS2Object
from jejune.activity_streams.collection import AS2Collection


class Foo(AS2Object):
    __jsonld_type__ = 'Foo'


class FooCollection(AS2Collection):
    __child_type__ = Foo


def test_collection():
    f1 = Foo(name='a')
    f2 = Foo(name='b')

    fc = FooCollection.new([f1, f2])
    fc_dict = fc.serialize(dict)

    assert fc_dict['@context'] == AS2Object.__jsonld_context__
    assert fc_dict['type'] == 'Collection'
    assert fc_dict['items'] == [f1.serialize(dict), f2.serialize(dict)]

    fc2 = FooCollection.deserialize(fc.serialize())
    assert fc.serialize() == fc2.serialize()