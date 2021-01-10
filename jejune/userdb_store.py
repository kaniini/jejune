import hashlib
import os


class UserDBStore:
    """
    The UserDBStore is a pseudo-filesystem which contains paths like:

        Users:kaniini:base
        Users:kaniini:inbox
        Users:kaniini:outbox

    These are stored in a tree of hashes, like the RDF store.
    """
    def __init__(self, app):
        self.app = app
        self.path = self.app.config['paths']['userdb']

    def __repr__(self):
        return "<User Store: {0}>".format(self.path)

    def hash_for_topic(self, namespace: str, topic: str, item: str) -> str:
        key = str().join([namespace, ':', topic, ":", item])
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def directory_for_hash(self, hashed: str) -> str:
        return '/'.join([self.path, hashed[0:2], hashed[2:4]])

    def path_for_hash(self, hashed: str) -> str:
        return '/'.join([self.directory_for_hash(hashed), hashed])

    def path_for_topic(self, namespace: str, topic: str, item: str) -> str:
        return self.path_for_hash(self.hash_for_topic(namespace, topic, item))

    def make_parents_for_hash(self, hashed: str):
        path_mode = 0o755
        os.makedirs(self.directory_for_hash(hashed), path_mode, True)

    def topic_exists(self, namespace: str, topic: str, item: str) -> bool:
        path = self.path_for_topic(namespace, topic, item)

        try:
            st = os.stat(path)
            return st.st_mtime > 0
        except:
            return False

    def fetch_topic(self, namespace: str, topic: str, item: str) -> str:
        if not self.topic_exists(namespace, topic, item):
            return None

        path = self.path_for_topic(namespace, topic, item)
        try:
            with open(path) as f:
                return f.read()
        except:
            return None

    def put_topic(self, namespace: str, topic: str, item: str, data: str):
        hashed = self.hash_for_topic(namespace, topic, item)
        path = self.path_for_hash(hashed)

        self.make_parents_for_hash(hashed)

        with open(path, 'w') as f:
            f.write(data)


class UserDBNamespace:
    def __init__(self, app, namespace: str, klass: type):
        self.app = app
        self.store = app.userdb_store
        self.namespace = namespace
        self.klass = klass

    def __repr__(self):
        return "<UserDBNamespace: {0} [{1}]>".format(self.namespace, self.klass.__name__)

    def fetch(self, topic: str, item: str) -> str:
        data = self.store.fetch_topic(self.namespace, topic, item)
        return self.klass.deserialize(data)

    def put(self, topic: str, item: str, object):
        self.store.put_topic(self.namespace, topic, item, object.serialize())