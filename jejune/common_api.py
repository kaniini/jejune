import asyncio
import logging


from .activity_streams.collection import AS2Collection
from .activity_streams.object import Note, Document
from .activity_pub.actor import Actor
from .activity_pub.verbs import Create


class CommonAPIError(Exception):
    def __init__(self, reason: str):
        self.reason = reason

    def __repr__(self) -> str:
        return '<CommonAPIError: {0}>'.format(self.reason)


class CommonAPI:
    def __init__(self, app):
        self.app = app
        asyncio.ensure_future(self.ensure_shared_inbox())

    async def ensure_shared_inbox(self):
        coll = AS2Collection.create_if_not_exists(self.app.shared_inbox_uri)

    def post(self, actor: Actor, **kwargs) -> Create:
        status = kwargs.get('status')
        if not status:
            return None

        scope = kwargs.get('visibility', 'public')
        media_ids = kwargs.get('media_ids', [])

        attachments = []
        for media_id in media_ids:
            hashed = media_id.split('.')[1]
            att = Document.fetch_from_hash(hashed)
            if att:
                attachments += [att]

        n = Note(content=status,
                 summary=kwargs.get('spoiler_text', None),
                 attributedTo=actor.id,
                 source={'content': status, 'mediaType': kwargs.get('content_type', 'text/plain')},
                 inReplyTo=None,
                 audience=self.audience_for_scope(scope, actor, []),
                 attachment=[att.serialize(dict) for att in attachments])

        c = Create(actor=actor.id,
                   object=n.id,
                   to=self.to_for_scope(scope, actor, []),
                   cc=self.cc_for_scope(scope, actor, []),
                   audience=n.audience)

        asyncio.ensure_future(c.apply_side_effects())

        return c

    def to_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        scopes = {
            'public': ['https://www.w3.org/ns/activitystreams#Public'],
            'unlisted': [actor.id, actor.followers],
            'direct': mentioned,
        }

        return scopes.get(scope, [])

    def cc_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        scopes = {
            'public': [actor.id, actor.followers],
            'unlisted': ['https://www.w3.org/ns/activitystreams#Public'],
            'direct': mentioned,
        }

        return scopes.get(scope, [])

    def audience_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        return self.to_for_scope(scope, actor, mentioned) + self.cc_for_scope(scope, actor, mentioned)

    def upload_media(self, actor: Actor, data: bytearray, filename: str, content_type: str) -> Document:
        exts = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'audio/mpeg': 'mp3',
            'video/mpeg': 'mp4',
        }

        uri = self.app.upload_uri(exts.get(content_type, 'bin'))
        filename = uri.split('/')[-1]
        fspath = self.app.config['paths']['upload'] + '/' + filename

        with open(fspath, 'wb') as f:
            f.write(data)

        a = Document(attributedTo=actor.id,
                     mediaType=content_type,
                     url=uri,
                     name=filename)
        logging.info('ID %s', a.id)

        return a