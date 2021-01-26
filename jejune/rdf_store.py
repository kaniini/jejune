from async_timeout import timeout

import aiohttp
import hashlib
import logging
import os
import simplejson
import time
import urllib.parse


from cachetools import TTLCache


class RDFStore:
    def __init__(self, app):
        self.app = app
        self.path = self.app.config['paths']['rdf']

        # XXX: make RDF filesystem cache parameters configurable
        self.cache = TTLCache(32768, 3600)

    def __repr__(self):
        return "<RDF Store: {0}>".format(self.path)

    def hash_for_uri(self, uri: str) -> str:
        parse_result = urllib.parse.urlparse(uri)

        base = [parse_result.netloc, ':', parse_result.path]
        if parse_result.fragment:
            base += ['#', parse_result.fragment]

        key = str().join(base)
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def directory_for_hash(self, hashed: str) -> str:
        return '/'.join([self.path, hashed[0:2], hashed[2:4]])

    def path_for_hash(self, hashed: str) -> str:
        return '/'.join([self.directory_for_hash(hashed), hashed])

    def path_for_uri(self, uri: str) -> str:
        return self.path_for_hash(self.hash_for_uri(uri))

    def make_parents_for_hash(self, hashed: str):
        path_mode = 0o755
        os.makedirs(self.directory_for_hash(hashed), path_mode, True)

    def uri_is_local(self, uri: str) -> bool:
        parse_result = urllib.parse.urlparse(uri)
        return parse_result.netloc == self.app.config['instance'].get('hostname')

    def local_uri_exists(self, uri: str) -> bool:
        if not self.uri_is_local(uri):
            return False

        return self.hash_exists(self.hash_for_uri(uri))

    def hash_exists(self, hashed: str) -> bool:
        path = self.path_for_hash(hashed)

        try:
            st = os.stat(path)
            return st.st_mtime > 0
        except:
            return False

    def overridden(self, uri: str) -> bool:
        hashed = self.hash_for_uri(uri)
        path = self.path_for_hash(hashed) + '.override'

        try:
            st = os.stat(path)
            return st.st_mtime > 0
        except:
            return False

    def override(self, uri: str):
        hashed = self.hash_for_uri(uri)
        path = self.path_for_hash(hashed) + '.override'

        self.make_parents_for_hash(hashed)

        logging.debug('RDF: Marking URI %r as overridden.', uri)

        with open(path, 'w') as f:
            pass

    def fetch_hash(self, hashed: str) -> (str, float):
        if hashed in self.cache:
            return self.cache[hashed]

        logging.debug('Fetching hash: %s', hashed)

        path = self.path_for_hash(hashed)

        logging.debug('Trying RDF store path: %s', path)

        try:
            st = os.stat(path)

            with open(path, 'r') as f:
                self.cache[hashed] = (f.read(), st.st_mtime)
                return self.cache[hashed]
        except:
            return (None, 0)

    def fetch_cached(self, uri: str) -> str:
        return self.fetch_hash(self.hash_for_uri(uri))

    def put_entry(self, uri: str, entry: str):
        hashed = self.hash_for_uri(uri)
        self.cache[hashed] = (entry, time.time())

        self.make_parents_for_hash(hashed)

        path = self.path_for_hash(hashed)
        with open(path, 'w') as f:
            f.write(entry)

    async def fetch_remote(self, uri: str) -> str:
        logging.debug('Fetching uncached remote object: %s', uri)

        headers = {
            'Accept': 'application/activity+json',
            'User-Agent': self.app.user_agent,
        }

        try:
            async with timeout(5.0):
                async with aiohttp.ClientSession() as session:
                    async with session.get(uri, headers=headers) as response:
                        if response.status != 200:
                            return None
                        return (await response.text())
        except:
            logging.info('Timeout while fetching remote object %r.', uri)

        return None

    async def fetch_remote_to_cache(self, uri: str) -> str:
        entry = await self.fetch_remote(uri)

        if not entry:
            return None

        self.put_entry(uri, entry)
        return entry

    async def fetch(self, uri: str) -> str:
        logging.debug('Fetching object: %s', uri)

        (entry, mtime) = self.fetch_cached(uri)

        logging.debug('Got %r from fetch_cached', entry)

        if self.uri_is_local(uri) or self.overridden(uri):
            logging.debug('Returning local object: %s', uri)
            return entry

        # XXX: make reupdate configurable
        if time.time() - mtime > 172800 or not entry:
            return (await self.fetch_remote_to_cache(uri))

        return entry

    async def fetch_json(self, uri: str) -> dict:
        entry = await self.fetch(uri)

        try:
            return simplejson.loads(entry)
        except:
            logging.info('Failed to load JSON from URI: %s', uri)
            return None

    def fetch_hash_json(self, hashed: str) -> dict:
        (entry, _) = self.fetch_hash(hashed)

        try:
            return simplejson.loads(entry)
        except:
            logging.info('Failed to load JSON from hash: %s', hashed)
            return None
