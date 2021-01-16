from . import AS2Object, AS2Pointer, registry
from ..activity_pub.actor import Actor


class Note(AS2Object):
    __jsonld_type__ = 'Note'

    def serialize_to_mastodon(self):
        actor = AS2Pointer(self.actor).dereference()

        reply = None
        reply_actor = None

        if self.inReplyTo:
            reply = AS2Pointer(self.inReplyTo).dereference()
            if reply:
                reply_actor = AS2Pointer(reply.actor).dereference()

        return {
            'id': self.storeIdentity,
            'created_at': self.published,
            'in_reply_to_id': getattr(reply, 'storeIdentity', None),
            'in_reply_to_account_id': getattr(reply_actor, 'storeIdentity', None),
            'sensitive': getattr(self, 'summary', None) is not None,
            'spoiler_text': getattr(self, 'summary', None),
            'visibility': 'public',    # XXX: scopes
            'language': 'en',          # XXX: languages
            'uri': self.id,
            'url': self.id,
            'replies_count': 0,        # XXX: replies collection
            'reblog_count': 0,         # XXX: reblog collection
            'favourites_count': 0,     # XXX: favourites collection
            'favourited': False,
            'reblogged': False,
            'muted': False,            # XXX: mutes
            'bookmarked': False,       # XXX: bookmarks
            'reblog': None,            # XXX: reblogs
            'application': {
                 'name': 'Web',
                 'website': None,
            },
            'account': actor.serialize_to_mastodon(),
            'media_attachments': [],   # XXX: attachments
            'mentions': [],            # XXX: mentions
            'tags': [],                # XXX: tags
            'emojis': [],              # XXX: emojis
            'card': {},
            'poll': None,
        }

registry.register_type(Note)