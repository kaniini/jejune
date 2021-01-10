from .user import User, Token, Mailbox
from .app import App
from .activity_pub.actor import Actor


class UserAPI:
    def __init__(self, app):
        self.app = app
        self.store = app.userns
        self.app_store = app.appns
        self.token_store = app.tokenns
        self.mailbox_store = app.mailboxns
        self.rdf_store = app.rdf_store

    def create_user(self, description: str, actor_type: str, username: str, email: str, password: str, bio: str, locked: bool) -> User:
        u = User.new(self.app, password,
                     description=description,
                     actor_type=actor_type,
                     username=username,
                     bio=bio,
                     email=email,
                     locked=locked)
        self.store.put(u.username, 'base', u)

        actor = Actor.new_from_user(u)
        self.rdf_store.put_entry(u.actor_uri, actor.serialize())

        inbox = Mailbox.new(u)
        self.mailbox_store.put(u.inbox_uri.split('/')[-1], 'inbox', inbox)

        outbox = Mailbox.new(u)
        self.mailbox_store.put(u.outbox_uri.split('/')[-1], 'outbox', outbox)

        return u

    def find_user(self, username: str) -> User:
        return self.store.fetch(username, 'base')

    def create_app(self, client_name: str, redirect_uris: str, website: str) -> App:
        app = App.new(client_name, redirect_uris, website)
        self.app_store.put(app.client_id, 'base', app)

        return app

    def find_app(self, client_id: str) -> App:
        return self.app_store.fetch(client_id, 'base')

    def login(self, user: User, app: App) -> Token:
        token = user.login(app)
        self.token_store.put(token.token, 'base', token)

        return token

    def find_login_from_token(self, token: str) -> Token:
        return self.token_store.fetch(token)