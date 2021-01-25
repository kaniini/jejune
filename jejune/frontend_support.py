from .activity_streams import AS2Object


class FrontendSupport:
    def friendly_uri(self, object: AS2Object) -> str:
        return object.id
