import asyncio
import pytest


from jejune import get_jejune_app
from jejune.activity_streams import AS2Pointer
from jejune.activity_streams.collection import AS2Collection
from jejune.activity_pub.actor import Person


from jejune_tests.helpers import create_user


@pytest.mark.asyncio
async def test_incoming_create():
    a = Person(id='https://test.example/users/abc',
               name='abc',
               inbox='https://test.example/users/abc/inbox',
               outbox='https://test.example/users/abc/outbox',
               preferredUsername='abc')

    message = {
        'type': 'Create',
        'to': ['https://www.w3.org/ns/activitystreams#Public'],
        'cc': [],
        'object': {
            'type': 'Note',
            'id': 'https://test.example/objects/1234',
            'content': 'Hi there!',
            'attributedTo': a.id,
        },
        'id': 'https://test.example/activities/5678',
        'actor': a.id,
    }

    await get_jejune_app().inbox_processor.process_item(message)
    await asyncio.sleep(0.1)

    obj = AS2Pointer(message['object']['id']).dereference()
    assert obj is not None

    assert obj.type == 'Note'
    assert obj.content == 'Hi there!'
    assert obj.attributedTo == a.id


@pytest.mark.asyncio
async def test_incoming_follow():
    a = Person(id='https://test.example/users/abc',
               name='abc',
               inbox='https://test.example/users/abc/inbox',
               outbox='https://test.example/users/abc/outbox',
               preferredUsername='abc')

    app = get_jejune_app()
    target = create_user()

    message = {
        'type': 'Follow',
        'object': target.actor().id,
        'actor': a.id,
        'to': [target.actor().id],
        'cc': [],
    }

    await get_jejune_app().inbox_processor.process_item(message)
    await asyncio.sleep(0.1)

    coll = AS2Pointer(target.actor().followers).dereference()
    assert isinstance(coll, AS2Collection)
    assert len(coll) == 1