from jejune.serializable import Serializable


def test_basic():
    class Foo(Serializable):
        pass

    f1 = Foo(name='a')
    assert f1.name == 'a'

    f2 = Foo(name='b')
    assert f1 != f2

    assert f1.serialize() == '{"name": "a"}'
    assert f2.serialize() == '{"name": "b"}'


def test_roundtrip():
    class Foo(Serializable):
        pass

    f1 = Foo(name='a')
    assert f1.name == 'a'

    assert Foo.deserialize(f1.serialize()).name == f1.name