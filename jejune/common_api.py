from .activity_streams.object import Note
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

    def post(self, actor: Actor, **kwargs) -> Create:
        status = kwargs.get('status')
        if not status:
            return None

        n = Note.new(content=status,
                     summary=kwargs.get('spoiler_text', None),
                     attributedTo=actor.id)

        c = Create.new(actor=actor.id,
                       object=n.id,
                       to=self.to_for_scope(scope, actor, []),
                       cc=self.cc_for_scope(scope, actor, []),
                       audience=self.audience_for_scope(scope, actor, []))

        return c

    def to_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        scopes = {
            'public': ['https://www.w3.org/ns/activitystreams#Public'],
            'unlisted': [actor.followers],
            'direct': mentioned,
        }

        return scopes.get(scope, [])

    def cc_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        scopes = {
            'public': [actor.followers],
            'unlisted': ['https://www.w3.org/ns/activitystreams#Public'],
            'direct': mentioned,
        }

        return scopes.get(scope, [])

    def audience_for_scope(self, scope: str, actor: Actor, mentioned: list) -> list:
        return self.to_for_scope(scope, actor, mentioned) + self.cc_for_scope(scope, actor, mentioned)