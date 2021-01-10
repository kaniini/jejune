import crypt
import uuid


from Crypto.PublicKey import RSA


from .serializable import Serializable


def generate_private_key():
    privkey = RSA.generate(4096)
    return privkey.exportKey('PEM').decode('utf-8')


class User(Serializable):
    @classmethod
    def new(cls, app, password: str, **kwargs) -> Serializable:
        crypted_pass = crypt.crypt(password, crypt.mksalt(crypt.METHOD_BLOWFISH))
        actor_uri = app.rdf_object_uri()

        kwargs['actor_uri'] = actor_uri
        kwargs['password'] = crypted_pass
        kwargs['privateKey'] = generate_private_key()

        return cls(**kwargs)

    def verify_password(self, password: str) -> bool:
        crypted_pass = crypt.crypt(password, self.password)
        return self.password == crypted_pass

    def get_public_key(self):
        assert self.privateKey

        privkey = RSA.importKey(self.privateKey)
        pubkey = privkey.publickey()

        return {
            'id': '#'.join([self.actor_uri, 'main-key']),
            'owner': self.actor_uri,
            'publicKeyPem': pubkey.exportKey('PEM').decode('utf-8')
        }

    def serialize_to_mastodon(self):
        return {
        }


class Token(Serializable):
    @classmethod
    def new(cls, user: User) -> Serializable:
        return cls(user=user.username, token=str(uuid.uuid4()))