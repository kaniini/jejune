import asyncio
import aiohttp.web


from .config import load_config
from .rdf_store import RDFStore
from .userdb_store import UserDBStore, UserDBNamespace
from .user import User


class Application(aiohttp.web.Application):
    def __init__(self, config: str):
        super(Application, self).__init__(middlewares=[])
        self.config = load_config(config)
        self.rdf_store = RDFStore(self)
        self.userdb_store = UserDBStore(self)
        self.userns = UserDBNamespace(self, 'User', User)
