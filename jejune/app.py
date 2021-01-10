import uuid


from .serializable import Serializable


class App(Serializable):
    @classmethod
    def new(cls, client_name: str, redirect_uris: str, website: str) -> Serializable:
        client_id = client_secret = cid = str(uuid.uuid4())

        return cls(name=client_name,
                   redirect_uri=redirect_uris,
                   website=website,
                   client_id=client_id,
                   client_secret=client_secret,
                   id=cid)