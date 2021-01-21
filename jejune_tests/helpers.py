import uuid


from jejune import get_jejune_app
from jejune.user import User
from jejune.activity_pub.actor import Actor


from Crypto.PublicKey import RSA


def generate_private_key():
    privkey = RSA.generate(1024)
    return privkey.exportKey('PEM').decode('utf-8')

TEST_KEY = generate_private_key()


def create_user(actor_type='Person'):
    app = get_jejune_app()

    u = User.new(app, None,
                 description=str(uuid.uuid4()),
                 actor_type='Person',
                 username=str(uuid.uuid4()).replace('-', ''),
                 bio='test user',
                 email='test@test.com',
                 locked=False,
                 privateKey=TEST_KEY)
    app.userns.put(u.username, 'base', u)

    actor = Actor.new_from_user(u)

    return u
