import asyncio


from .user import User, Token, Mailbox
from .app import App
from .activity_pub.actor import Actor
from .activity_pub.verbs import Follow, Undo
from .webfinger_client import WebfingerClient


class UserAPI:
    def __init__(self, app):
        self.app = app
        self.store = app.userns
        self.app_store = app.appns
        self.token_store = app.tokenns
        self.mailbox_store = app.mailboxns
        self.rdf_store = app.rdf_store
        self.webfinger = WebfingerClient(self.app)

    def create_user(self, description: str, actor_type: str, username: str, email: str, password: str, bio: str, locked: bool) -> User:
        if self.find_user(username):
            return None

        u = User.new(self.app, password,
                     description=description,
                     actor_type=actor_type,
                     username=username,
                     bio=bio,
                     email=email,
                     locked=locked)
        self.store.put(u.username, 'base', u)

        actor = Actor.new_from_user(u)

        inbox = Mailbox.new(u)
        self.mailbox_store.put(u.inbox_uri.split('/')[-1], 'inbox', inbox)

        outbox = Mailbox.new(u)
        self.mailbox_store.put(u.outbox_uri.split('/')[-1], 'outbox', outbox)

        return u

    async def discover_user(self, username: str) -> User:
        u = self.store.fetch(username, 'base')
        if u:
            return u

        actor = await self.webfinger.discover_actor(username)
        if actor:
            u = await actor.synchronize()
            return u

        return None

    def find_user(self, username: str) -> User:
        return self.store.fetch(username, 'base')

    def create_app(self, client_name: str, redirect_uris: str, website: str) -> App:
        app = App.new(client_name, redirect_uris, website)
        self.app_store.put(app.client_id, 'base', app)

        return app

    def find_app(self, client_id: str) -> App:
        return self.app_store.fetch(client_id, 'base')

    def login(self, user: User) -> Token:
        token = user.login()
        self.token_store.put(token.access_token, 'base', token)

        return token

    def find_token(self, access_token: str) -> Token:
        return self.token_store.fetch(access_token, 'base')

    def find_login_from_token(self, access_token: str) -> User:
        token = self.find_token(access_token)
        if not token:
            return None

        return self.find_user(token.user)

    def update_avatar(self, user: User, data: bytearray, content_type: str):
        exts = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
        }

        actor = user.actor()
        uri = self.app.upload_uri(exts.get(content_type, 'bin'))
        filename = uri.split('/')[-1]
        fspath = self.app.config['paths']['upload'] + '/' + filename

        with open(fspath, 'wb') as f:
            f.write(data)

        actor.icon = {
            'type': 'Image',
            'mediaType': content_type,
            'url': uri,
        }
        actor.commit()
        asyncio.ensure_future(actor.announce_update())

    def follow(self, follower: Actor, followee: Actor):
        f = Follow(actor=follower.id, object=followee.id, to=[followee.id])

        asyncio.ensure_future(f.apply_side_effects())
        return f

    # XXX: figure out what our actual follow activity ID was...
    # one approach would be to have a mutations collection which serves
    # as a log.
    def unfollow(self, follower: Actor, followee: Actor):
        u = Undo(actor=follower.id, object={
            'type': 'Follow',
            'actor': follower.id,
            'object': followee.id,
            'id': self.app.rdf_object_uri()
        })

        asyncio.ensure_future(u.apply_side_effects())
        return u
