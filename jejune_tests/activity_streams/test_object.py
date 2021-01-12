from jejune.activity_streams import AS2Object


def test_object():
    class TestObject(AS2Object):
        __jsonld_type__ = 'TestObject'

    foo = TestObject(name='Foo')
    foo_dict = foo.serialize(dict)

    assert foo_dict['@context'] == AS2Object.__jsonld_context__
    assert foo_dict['type'] == 'TestObject'
    assert foo_dict['name'] == 'Foo'

    assert foo.serialize() == '{"@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"], "name": "Foo", "type": "TestObject"}'

    foo2 = TestObject.deserialize(foo.serialize())
    assert foo.serialize() == foo2.serialize()