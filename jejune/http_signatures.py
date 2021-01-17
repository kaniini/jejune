import aiohttp
import aiohttp.web
import base64
import logging


from Crypto.PublicKey import RSA
from Crypto.Hash import SHA, SHA256, SHA512
from Crypto.Signature import PKCS1_v1_5


class HTTPSignatureVerifier:
    hashes = {
        'sha1': SHA,
        'sha256': SHA256,
        'sha512': SHA512,
    }

    def split_signature(self, sig: str) -> dict:
        default = {"headers": "date"}

        sig = sig.strip().split(',')

        for chunk in sig:
            k, _, v = chunk.partition('=')
            v = v.strip('\"')
            default[k] = v

        default['headers'] = default['headers'].split()
        return default

    async def load_key(self, actor_uri: str) -> RSA:
        from .activity_streams import AS2Pointer
        actor_uri = AS2Pointer(actor_uri).serialize()

        from .activity_pub.actor import Actor
        actor = await Actor.fetch_from_uri(actor_uri)
        if not actor:
            return None

        try:
            return RSA.importKey(actor.publicKey['publicKeyPem'])
        except:
            return None

    def build_signing_string(self, headers: dict, used_headers: list) -> str:
        return '\n'.join(map(lambda x: ': '.join([x.lower(), headers[x]]), used_headers))

    async def validate(self, actor_uri: str, request) -> bool:
        pubkey = await self.load_key(actor_uri)
        if not pubkey:
            return False

        headers = request.headers.copy()
        headers['(request-target)'] = ' '.join([request.method.lower(), request.path])

        sig = self.split_signature(headers['signature'])
        sigstring = self.build_signing_string(headers, sig['headers'])

        sign_alg, _, hash_alg = sig['algorithm'].partition('-')
        sigdata = base64.b64decode(sig['signature'])

        pkcs = PKCS1_v1_5.new(pubkey)
        h = self.hashes[hash_alg].new()
        h.update(sigstring.encode('utf-8'))
        result = pkcs.verify(h, sigdata)

        request['validated'] = result

        logging.debug('validates? %r', result)
        return result


class HTTPSignatureSigner:
    def sign(self, headers: dict, key: RSA, key_id: str) -> str:
        headers = {x.lower(): y for x, y in headers.items()}
        used_headers = headers.keys()

        sig = {
            'keyId': key_id,
            'algorithm': 'rsa-sha256',
            'headers': ' '.join(used_headers)
        }

        sigstring = self.build_signing_string(headers, used_headers)
        sig['signature'] = self.sign_signing_string(sigstring, key)

        chunks = ['{}="{}"'.format(k, v) for k, v in sig.items()]
        return ','.join(chunks)

    def build_signing_string(self, headers: dict, used_headers: list) -> str:
        return '\n'.join(map(lambda x: ': '.join([x.lower(), headers[x]]), used_headers))

    def sign_signing_string(self, sigstring: str, key: RSA) -> str:
        pkcs = PKCS1_v1_5.new(key)
        h = SHA256.new()
        h.update(sigstring.encode('utf-8'))
        sigdata = pkcs.sign(h)

        sigdata = base64.b64encode(sigdata)
        return sigdata.decode('utf-8')