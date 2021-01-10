import asyncio
import aiohttp.web
import uuid


from .config import load_config
from .rdf_store import RDFStore
from .userdb_store import UserDBStore, UserDBNamespace
from .user import User
from .app import App
from .user_api import UserAPI


class Application(aiohttp.web.Application):
    def __init__(self, config: str):
        super(Application, self).__init__(middlewares=[])
        self.config = load_config(config)
        self.rdf_store = RDFStore(self)
        self.userdb_store = UserDBStore(self)
        self.userns = UserDBNamespace(self, 'User', User)
        self.appns = UserDBNamespace(self, 'App', App)
        self.userapi = UserAPI(self)

    @property
    def hostname(self):
        return self.config['instance']['hostname']

    def rdf_object_uri(self):
        while True:
            object_uuid = str(uuid.uuid4())

            uri = self.rdf_object_uri_for(object_uuid)
            if not self.rdf_store.local_uri_exists(uri):
                return uri

    def rdf_object_uri_for(self, object_uuid):
        return str().join(['https://', self.hostname, '/.well-known/jejune/object/', object_uuid])