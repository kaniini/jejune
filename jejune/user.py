import crypt
import time
import uuid


from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


from .serializable import Serializable


def generate_private_key():
    privkey = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    return privkey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())


class User(Serializable):
    @classmethod
    def new(cls, app, password: str, **kwargs) -> Serializable:
        if password:
            crypted_pass = crypt.crypt(password, crypt.mksalt(crypt.METHOD_BLOWFISH))
        else:
            crypted_pass = None

        actor_uri = app.rdf_object_uri()

        kwargs['actor_uri'] = actor_uri
        kwargs['password'] = crypted_pass
        kwargs['shared_inbox_uri'] = app.shared_inbox_uri
        kwargs['inbox_uri'] = app.inbox_uri()
        kwargs['outbox_uri'] = app.outbox_uri()
        kwargs['followers_uri'] = app.object_uri('collection')
        kwargs['following_uri'] = app.object_uri('collection')
        kwargs['petname'] = app.username_to_petname(kwargs['username'])

        if 'privateKey' not in kwargs:
            kwargs['privateKey'] = generate_private_key()

        return cls(**kwargs)

    def verify_password(self, password: str) -> bool:
        crypted_pass = crypt.crypt(password, self.password)
        return self.password == crypted_pass

    def get_public_key(self):
        privkey = self.privkey()
        pubkey = privkey.public_key()
        pem = pubkey.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

        return {
            'id': '#'.join([self.actor_uri, 'main-key']),
            'owner': self.actor_uri,
            'publicKeyPem': pem,
        }

    def privkey(self) -> object:
        assert self.privateKey

        return serialization.load_pem_private_key(self.privateKey, password=None)

    def serialize_to_mastodon(self):
        return self.actor().serialize_to_mastodon()

    def login(self):
        return Token.new(self)

    def actor(self):
        from .activity_pub.actor import Actor
        return Actor.fetch_cached_from_uri(self.actor_uri)


class Mailbox(Serializable):
    @classmethod
    def new(cls, user: User) -> Serializable:
        return cls(user=user.username)


class Token(Serializable):
    @classmethod
    def new(cls, user: User) -> Serializable:
        return cls(user=user.username,
                   token_type='Bearer',
                   access_token=str(uuid.uuid4()),
                   refresh_token=str(uuid.uuid4()),
                   scope="read write follow",
                   expires_in=9999999999,
                   created_at=time.time(),
                   me=user.actor_uri)
