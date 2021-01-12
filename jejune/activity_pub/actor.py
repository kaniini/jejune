from ..activity_streams import AS2Object
from ..activity_streams.collection import AS2Collection
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
               'following': user.following_uri,
               'followers': user.followers_uri,
               'endpoints': {
                   'sharedInbox': user.shared_inbox_uri,
               },
               'petName': user.username}
        actor = cls(**obj)
        actor.fixate()
        return actor

    def fixate(self):
        AS2Collection.create_if_not_exists(self.inbox)
        AS2Collection.create_if_not_exists(self.outbox)
        AS2Collection.create_if_not_exists(self.following)
        AS2Collection.create_if_not_exists(self.followers)


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