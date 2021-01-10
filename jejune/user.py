import crypt


from .serializable import Serializable


class User(Serializable):
    @classmethod
    def new(cls, app, username: str, email: str, password: str) -> Serializable:
        crypted_pass = crypt.crypt(password, crypt.mksalt(crypt.METHOD_BLOWFISH))
        actor_uri = app.rdf_object_uri()

        return cls(username=username, email=email, password=crypted_pass, actor_uri=actor_uri)

    def verify_password(self, password: str) -> bool:
        crypted_pass = crypt.crypt(password, self.password)
        return self.password == crypted_pass