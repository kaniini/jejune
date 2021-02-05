import logging
import urllib.parse


from ..activity_streams import AS2Object, registry, AS2_PUBLIC
from ..activity_streams.collection import AS2Collection, collection_intersects
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
               'petName': user.username}
        actor = cls(**obj)
        actor.update_endpoints()
        actor.fixate()
        return actor

    def update_endpoints(self):
        from .. import get_jejune_app

        app = get_jejune_app()

        if self.remote():
            return

        self.endpoints = {
            'sharedInbox': app.shared_inbox_uri,
            'sharedOutbox': app.shared_outbox_uri,
            'oauthAuthorizationEndpoint': app.make_well_known_uri('oauth/authorize'),
            'oauthRegistrationEndpoint': app.make_well_known_uri('oauth/register'),
            'oauthTokenEndpoint': app.make_well_known_uri('oauth/token'),
            'uploadMedia': app.make_well_known_uri('media'),
        }

        self.commit()

    def best_inbox(self):
        return getattr(self, 'endpoints', {}).get('sharedInbox', self.inbox)

    def override_collections(self):
        from .. import get_jejune_app

        inbox = getattr(self, 'inbox', None)
        if inbox:
            get_jejune_app().rdf_store.override(inbox)

        outbox = getattr(self, 'outbox', None)
        if outbox:
            get_jejune_app().rdf_store.override(outbox)

        following = getattr(self, 'following', None)
        if following:
            get_jejune_app().rdf_store.override(following)

        followers = getattr(self, 'followers', None)
        if followers:
            get_jejune_app().rdf_store.override(followers)

    def fixate(self):
        self.override_collections()

        inbox = getattr(self, 'inbox', None)
        if inbox:
            AS2Collection.create_if_not_exists(inbox)

        outbox = getattr(self, 'outbox', None)
        if outbox:
            AS2Collection.create_if_not_exists(outbox)

        following = getattr(self, 'following', None)
        if following:
            AS2Collection.create_if_not_exists(following)

        followers = getattr(self, 'followers', None)
        if followers:
            AS2Collection.create_if_not_exists(followers)

    def avatar_icon(self):
        avatar = getattr(self, 'icon', {})
        return avatar.get('url', None)

    def serialize_to_mastodon(self):
        avatar = getattr(self, 'icon', {})
        banner = getattr(self, 'image', {})

        return {
            'id': self.storeIdentity,
            'username': self.preferredUsername,
            'acct': self.make_petname(),
            'locked': getattr(self, 'manuallyApprovesFollowers', False),
            'note': getattr(self, 'summary', ''),
            'url': self.id,
            'avatar': avatar.get('url', None),
            'avatar_static': avatar.get('url', None),
            'header': banner.get('url', None),
            'header_static': banner.get('url', None),
            'emojis': [],
            'fields': [],
            'display_name': self.name,
            'bot': self.type in ['Application', 'Service'],
            'following_count': 0,
        }

    async def announce_update(self):
        from .verbs import Update

        u = Update(object=self.serialize(), to=[AS2_PUBLIC, self.followers])
        await u.publish()

    def user(self) -> User:
        from .. import get_jejune_app
        return get_jejune_app().userapi.find_user(self.petName)

    def make_petname(self) -> str:
        if getattr(self, 'petName', None):
            return self.petName

        uri = urllib.parse.urlsplit(self.id)
        self.petName = f'{self.preferredUsername}@{uri.netloc}'
        self.commit()

        return self.petName

    async def synchronize(self):
        from .. import get_jejune_app

        self.update_endpoints()

        app = get_jejune_app()
        if app.userns.exists(self.make_petname(), 'base'):
            return

        self.fixate()

        if self.local():
            return

        if not getattr(self, 'preferredUsername'):
            return

        logging.debug('Synchronizing user store entry for actor %s', self.id)

        u = User(actor_uri=self.id, username=self.make_petname(), remote=True)
        get_jejune_app().userns.put(u.username, 'base', u)

        return u

    def mastodon_relationships_with(self, target):
        return {
            'id': target.mastodon_id(),
            'following': collection_intersects(target.followers, self.id),
            'requested': False,            # XXX
            'endorsed': False,             # XXX
            'followed_by': collection_intersects(self.followers, target.id),
            'muting': False,               # XXX
            'muting_notifications': False, # XXX
            'showing_reblogs': True,       # XXX
            'blocking': False,             # XXX
            'blocked_by': False,           # XXX
            'domain_blocking': False,      # XXX
            'note': '',                    # XXX: WTF is this for?
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
