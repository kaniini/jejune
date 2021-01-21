class Formatter:
    def __init__(self, app):
        self.app = app

    async def format(self, message: str, content_type: str) -> str:
        return message