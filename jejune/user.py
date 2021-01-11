import crypt
import time
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
        kwargs['shared_inbox_uri'] = app.shared_inbox_uri
        kwargs['inbox_uri'] = app.inbox_uri()
        kwargs['outbox_uri'] = app.outbox_uri()

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
            'id': self.username,
            'username': self.username,
            'acct': self.username,
            'locked': self.locked,
            'note': self.bio,
            'url': self.actor_uri,
            'avatar': getattr(self, 'avatar', None),
            'avatar_static': getattr(self, 'avatar_static', None),
            'header': getattr(self, 'header', None),
            'header_static': getattr(self, 'header_static', None),
            'emojis': [],
            'fields': [],
            'display_name': self.description,
            'bot': self.actor_type in ['Application', 'Service'],
            'following_count': 0,
        }

    def login(self):
        return Token.new(self)


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
                   scopes="read write follow",
                   expires_in=9999999999,
                   created_at=time.time())