import logging
import markdown


from . import AS2Object, AS2Pointer, registry
from ..activity_pub.actor import Actor


class Note(AS2Object):
    __jsonld_type__ = 'Note'

    def __init__(self, **kwargs):
        if 'content' not in kwargs and 'source' in kwargs:
            source = kwargs['source']

            # XXX: run this through the real formatter
            if isinstance(source, dict):
                kwargs['content'] = markdown.markdown(source['content'])
            elif isinstance(source, str):
                kwargs['content'] = markdown.markdown(source)

        super().__init__(**kwargs)

    def mastodon_id(self):
        return '{0:d}.{1}'.format(int(self.published_ts()), self.storeIdentity)

    def serialize_to_mastodon(self):
        actor = AS2Pointer(self.attributedTo).dereference()

        reply = self.reply()
        reply_actor = getattr(reply, 'attributedTo', None)

        return {
            'id': self.mastodon_id(),
            'created_at': self.published,
            'in_reply_to_id': reply.mastodon_id() if reply else None,
            'in_reply_to_account_id': getattr(reply_actor, 'storeIdentity', None),
            'sensitive': getattr(self, 'summary', None) is not None,
            'spoiler_text': getattr(self, 'summary', None) or '',
            'content': getattr(self, 'content', None),
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
            'media_attachments': self.serialize_attachments_to_mastodon(),
            'mentions': [],            # XXX: mentions
            'tags': [],                # XXX: tags
            'emojis': [],              # XXX: emojis
            'card': None,
            'poll': None,
        }

    def serialize_attachment_to_mastodon(self, att) -> dict:
        return AS2Pointer(att).dereference().serialize_to_mastodon()

    def serialize_attachments_to_mastodon(self):
        attachment = getattr(self, 'attachment', [])
        return [self.serialize_attachment_to_mastodon(att) for att in attachment]

registry.register_type(Note)


class Document(AS2Object):
    __jsonld_type__ = 'Document'

    def mastodon_id(self):
        return '{0:d}.{1}'.format(int(self.published_ts()), self.storeIdentity)

    def serialize_to_mastodon(self):
        mediatype = self.mediaType.split('/')[0]
        if mediatype not in ['image', 'audio', 'video']:
            mediatype = 'unknown'

        return {
            'id': self.mastodon_id(),
            'type': mediatype,
            'url': self.url,
            'preview_url': self.url,
        }

registry.register_type(Document)


class Image(AS2Object):
    __jsonld_type__ = 'Image'

    def mastodon_id(self):
        return '{0:d}.{1}'.format(int(self.published_ts()), self.storeIdentity)

    def serialize_to_mastodon(self):
        mediatype = self.mediaType.split('/')[0]
        if mediatype not in ['image', 'audio', 'video']:
            mediatype = 'unknown'

        return {
            'id': self.mastodon_id(),
            'type': mediatype,
            'url': self.url,
            'preview_url': self.url,
        }

registry.register_type(Image)
