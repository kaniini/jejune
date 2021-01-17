from ..activity_streams import AS2Object, registry
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

    def best_inbox(self):
        return getattr(self, 'endpoints', {}).get('sharedInbox', self.inbox)

    def fixate(self):
        AS2Collection.create_if_not_exists(self.inbox)
        AS2Collection.create_if_not_exists(self.outbox)
        AS2Collection.create_if_not_exists(self.following)
        AS2Collection.create_if_not_exists(self.followers)

    def serialize_to_mastodon(self):
        avatar = getattr(self, 'icon', {})

        return {
            'id': self.storeIdentity,
            'username': self.preferredUsername,
            'acct': self.petName,
            'locked': self.manuallyApprovesFollowers,
            'note': self.summary,
            'url': self.id,
            'avatar': avatar.get('href', None),
            'avatar_static': avatar.get('href', None),
            'header': getattr(self, 'header', None),
            'header_static': getattr(self, 'header_static', None),
            'emojis': [],
            'fields': [],
            'display_name': self.name,
            'bot': self.type in ['Application', 'Service'],
            'following_count': 0,
        }


class Person(Actor):
    __jsonld_type__ = 'Person'


class Organization(Actor):
    __jsonld_type__ = 'Organization'


class Application(Actor):
    __jsonld_type__ = 'Application'


class Service(Actor):
    __jsonld_type__ = 'Service'


class Group(Actor):
    __jsonld_type__ = 'Group'


registry.register_type(Person)
registry.register_type(Organization)
registry.register_type(Application)
registry.register_type(Service)
registry.register_type(Group)