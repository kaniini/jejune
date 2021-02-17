import aiohttp
import aiohttp.web
import base64
import logging


from cryptography.hazmat.primitives.asymmetric import rsa, utils, padding
from cryptography.hazmat.primitives import hashes, serialization


class HTTPSignatureSigningStringMixIn:
    "A class which provides build_signing_string() and sign_signing_string()."
    def build_signing_string(self, headers: dict, used_headers: list) -> str:
        return '\n'.join(map(lambda x: ': '.join([x.lower(), headers[x]]), used_headers))

    def sign_signing_string(self, sigstring: str, key: object) -> str:
        sigdata = key.sign(sigstring.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
        sigdata = base64.b64encode(sigdata)
        return sigdata.decode('utf-8')


class HTTPSignatureVerifier(HTTPSignatureSigningStringMixIn):
    hashes = {
        'sha1': hashes.SHA1,
        'sha256': hashes.SHA256,
        'sha512': hashes.SHA512,
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

    def load_pem_public_key(self, key_data: str) -> object:
        return serialization.load_pem_public_key(key_data.encode('utf-8'))

    async def load_key(self, key_id: str) -> object:
        raise NotImplementedError()

    async def validate(self, request) -> bool:
        headers = request.headers.copy()
        headers['(request-target)'] = ' '.join([request.method.lower(), request.path])

        sig = self.split_signature(headers['signature'])
        sigstring = self.build_signing_string(headers, sig['headers'])

        sign_alg, _, hash_alg = sig['algorithm'].partition('-')
        sigdata = base64.b64decode(sig['signature'])

        pubkey = await self.load_key(sig['keyId'])
        if not pubkey:
            return False

        try:
            pubkey.verify(sigdata, sigstring.encode('utf-8'), padding.PKCS1v15(), self.hashes[hash_alg]())
            request['validated'] = True
            return True
        except:
            request['validated'] = False
            return False


class HTTPLegacySignatureSigner(HTTPSignatureSigningStringMixIn):
    def sign(self, headers: dict, key: object, key_id: str) -> dict:
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
        signed_headers = {'signature': ','.join(chunks)}

        headers.pop('(request-target)')
        headers.pop('host')

        signed_headers.update(headers)
        return signed_headers


# TODO: Implement new-style signatures as HTTPSignatureSigner.
HTTPSignatureSigner = HTTPLegacySignatureSigner
