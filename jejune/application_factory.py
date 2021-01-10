import aiohttp.web


from .config import load_config


class Application(aiohttp.web.Application):
    def __init__(self, config: str):
        super(Application, self).__init__(middlewares=[])
        self.config = load_config(config)
