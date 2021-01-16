from .activity_streams.object import Note
from .activity_pub.verbs import Create


class CommonAPI:
    def __init__(self, app):
        self.app = app

    def post(self, **kwargs):
        pass