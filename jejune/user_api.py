from .user import User
from .app import App
from .activity_pub.actor import Actor


class UserAPI:
    def __init__(self, app):
        self.app = app
        self.store = app.userns
        self.app_store = app.appns
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

        return u

    def find_user(self, username: str) -> User:
        return self.store.fetch(username, 'base')

    def create_app(self, client_name: str, redirect_uris: str, website: str) -> App:
        app = App.new(client_name, redirect_uris, website)
        self.app_store.put(app.client_id, 'base', app)

        return app

    def find_app(self, client_id: str) -> App:
        return self.app_store.fetch(client_id, 'base')