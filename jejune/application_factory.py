import asyncio
import aiohttp.web
import uuid


from .config import load_config
from .rdf_store import RDFStore
from .userdb_store import UserDBStore, UserDBNamespace
from .user import User, Token
from .app import App
from .user_api import UserAPI
from .common_api import CommonAPI
from .formatter import Formatter
from .workers.publisher import PublisherWorker
from .workers.inbox_processor import InboxProcessorWorker
from .workers.outbox_processor import OutboxProcessorWorker


from .middleware.oauth import oauth_middleware
from .middleware.http_signatures import http_signatures_middleware


from .frontend_support import FrontendSupport


class Application(aiohttp.web.Application):
    def __init__(self, config: str):
        super(Application, self).__init__(middlewares=[
            oauth_middleware,
            http_signatures_middleware,
        ])
        self.config = load_config(config)
        self.rdf_store = RDFStore(self)
        self.userdb_store = UserDBStore(self)
        self.userns = UserDBNamespace(self, 'User', User)
        self.appns = UserDBNamespace(self, 'App', App)
        self.tokenns = UserDBNamespace(self, 'Token', Token)
        self.userapi = UserAPI(self)
        self.commonapi = CommonAPI(self)
        self.formatter = Formatter(self)
        self.publisher = PublisherWorker(self)
        self.inbox_processor = InboxProcessorWorker(self)
        self.outbox_processor = OutboxProcessorWorker(self)
        self.frontend_support = FrontendSupport()
        self.ensure_instance_actor()

    @property
    def hostname(self):
        return self.config['instance']['hostname']

    def object_uri(self, object_type: str) -> str:
        while True:
            object_uuid = str(uuid.uuid4())

            uri = self.object_uri_for(object_uuid, object_type)
            if not self.rdf_store.local_uri_exists(uri):
                return uri

    def make_well_known_uri(self, path: str) -> str:
        return str().join(['https://', self.hostname, '/.well-known/jejune/', path])

    def object_uri_for(self, object_uuid: str, object_type: str) -> str:
        return str().join(['https://', self.hostname, '/.well-known/jejune/', object_type, '/', object_uuid])

    def rdf_object_uri(self) -> str:
        return self.object_uri('object')

    @property
    def shared_inbox_uri(self):
        return str().join(['https://', self.hostname, '/.well-known/jejune/sharedinbox'])

    @property
    def shared_outbox_uri(self):
        return str().join(['https://', self.hostname, '/.well-known/jejune/sharedoutbox'])

    @property
    def max_timeline_length(self):
        return self.config['instance']['limits']['timeline-length']

    def inbox_uri(self) -> str:
        return self.object_uri('inbox')

    def outbox_uri(self) -> str:
        return self.object_uri('outbox')

    def username_to_petname(self, username: str) -> str:
        return '@'.join([username, self.hostname])

    def upload_uri(self, ext) -> str:
        return '.'.join([self.object_uri('upload'), ext])

    @property
    def user_agent(self) -> str:
        from . import __version__
        return f'Jejune {__version__} (https://{self.hostname})'

    def load_plugins(self):
        [__import__(pkg) for pkg in self.config['instance'].get('plugins', [])]

    def ensure_instance_actor(self):
        self.userapi.create_user('Instance actor.', 'Application', 'internal.actor', None, None, None, False, self.make_well_known_uri('actor'))

    def instance_actor(self):
        u = self.userapi.find_user('internal.actor')
        return u
