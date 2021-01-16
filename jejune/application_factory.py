import asyncio
import aiohttp.web
import uuid


from .config import load_config
from .rdf_store import RDFStore
from .userdb_store import UserDBStore, UserDBNamespace
from .user import User, Token, Mailbox
from .app import App
from .user_api import UserAPI
from .common_api import CommonAPI
from .workers.publisher import PublisherWorker


from .middleware.oauth import oauth_middleware


class Application(aiohttp.web.Application):
    def __init__(self, config: str):
        super(Application, self).__init__(middlewares=[oauth_middleware])
        self.config = load_config(config)
        self.rdf_store = RDFStore(self)
        self.userdb_store = UserDBStore(self)
        self.userns = UserDBNamespace(self, 'User', User)
        self.appns = UserDBNamespace(self, 'App', App)
        self.tokenns = UserDBNamespace(self, 'Token', Token)
        self.mailboxns = UserDBNamespace(self, 'Mailbox', Mailbox)
        self.userapi = UserAPI(self)
        self.commonapi = CommonAPI(self)
        self.publisher = PublisherWorker(self)

    @property
    def hostname(self):
        return self.config['instance']['hostname']

    def object_uri(self, object_type: str) -> str:
        while True:
            object_uuid = str(uuid.uuid4())

            uri = self.object_uri_for(object_uuid, object_type)
            if not self.rdf_store.local_uri_exists(uri):
                return uri

    def object_uri_for(self, object_uuid: str, object_type: str) -> str:
        return str().join(['https://', self.hostname, '/.well-known/jejune/', object_type, '/', object_uuid])

    def rdf_object_uri(self) -> str:
        return self.object_uri('object')

    @property
    def shared_inbox_uri(self):
        return str().join(['https://', self.hostname, '/.well-known/jejune/sharedinbox'])

    def inbox_uri(self) -> str:
        return self.object_uri('inbox')

    def outbox_uri(self) -> str:
        return self.object_uri('outbox')

    def username_to_petname(self, username: str) -> str:
        return '@'.join([username, self.hostname])