from ..activity_streams import AS2Object
from ..user import User


class Actor(AS2Object):
    @classmethod
    def new_from_user(cls, user: User) -> AS2Object:
        obj = {'name': user.description,
               'type': user.actor_type,
               'preferredUsername': user.username,
               'id': user.actor_uri,
               'summary': user.bio,
               'manuallyApprovesFollowers': user.locked,
               'publicKey': user.get_public_key(),
               'inbox': user.inbox_uri,
               'outbox': user.outbox_uri,
               'sharedInbox': user.shared_inbox_uri}
        return cls(**obj)


class Person(Actor):
    pass


class Organization(Actor):
    pass


class Application(Actor):
    pass


class Service(Actor):
    pass


class Group(Actor):
    pass