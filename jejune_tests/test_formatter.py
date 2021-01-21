import pytest


from jejune import get_jejune_app
from jejune_tests.helpers import create_user


def test_linebreak():
    fmt = get_jejune_app().formatter
    assert fmt.linebreak('a\nb\nc') == 'a<br>\nb<br>\nc'


def test_tokenize_mentions():
    fmt = get_jejune_app().formatter

    assert fmt.tokenize_mentions('@foo @bar @baz') == ['@foo', '@bar', '@baz']
    assert fmt.tokenize_mentions('hi there @foo @bar @baz') == ['hi there ', '@foo', '@bar', '@baz']
    assert fmt.tokenize_mentions('@foo hey @bar hi @baz whats up') == ['@foo', 'hey ', '@bar', 'hi ', '@baz', 'whats up']


@pytest.mark.asyncio
async def test_replace_mentions():
    fmt = get_jejune_app().formatter

    u1 = create_user()
    u2 = create_user()
    u3 = create_user()

    message = f'@{u1.username} hi there!'
    new_msg, mentions = await fmt.replace_mentions(message)

    assert 'class="u-url mention"' in new_msg
    assert [u.id for u in mentions] == [u1.actor().id]

    message = f'@{u1.username} @{u2.username} whats up'
    new_msg, mentions = await fmt.replace_mentions(message)

    assert 'class="u-url mention"' in new_msg
    assert [u.id for u in mentions] == [u1.actor().id, u2.actor().id]

    message = f'@{u1.username} @{u2.username} @{u3.username} hey!'
    new_msg, mentions = await fmt.replace_mentions(message)

    assert 'class="u-url mention"' in new_msg
    assert [u.id for u in mentions] == [u1.actor().id, u2.actor().id, u3.actor().id]


@pytest.mark.asyncio
async def test_format():
    fmt = get_jejune_app().formatter

    u1 = create_user()

    message = f'@{u1.username} how are you?'
    new_msg = await fmt.format(message, 'text/plain')

    assert 'class="u-url mention"' in new_msg
