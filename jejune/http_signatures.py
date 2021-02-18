import aiohttp
import aiohttp.web
import base64
import logging


from cryptography.hazmat.primitives.asymmetric import rsa, utils, padding
from cryptography.hazmat.primitives import hashes, serialization


class HTTPSignatureSigningStringMixIn:
    "A class which provides build_signing_string()."
    def build_signing_string(self, headers: dict, used_headers: list) -> str:
        return '\n'.join(map(lambda x: ': '.join([x.lower(), headers[x]]), used_headers))


class HTTPSignatureMechanism:
    "A class which describes the behavior of a signature mechanism."
    def verify(self, pubkey: object, sigdata: bytes, sigstring: bytes, algorithm: str) -> bool:
        """
        Verify a signature, given the public key, signature data, generated signature string and
        algorithm (for legacy implementations).

        Returns True if the signature is valid, else False.
        """
        raise NotImplementedError()

    def sign(self, sigstring: bytes, privkey: object) -> str:
        """
        Generates a signature payload, given the signing string and private key.
        """
        raise NotImplementedError()


class GenericSignatureMechanism(HTTPSignatureMechanism):
    padding_mechanism = padding.PKCS1v15
    hash_mechanism = None

    def verify(self, pubkey: object, sigdata: bytes, sigstring: bytes, algorithm: str) -> bool:
        try:
            pubkey.verify(sigdata, sigstring, self.padding_mechanism(), self.hash_mechanism())
            return True
        except:
            return False

    def sign(self, sigstring: bytes, privkey: object) -> str:
        sigdata = privkey.sign(sigstring, self.padding_mechanism(), self.hash_mechanism())
        sigdata = base64.b64encode(sigdata)
        return sigdata.decode('utf-8')


class Legacy_RSA_SHA1_Mechanism(GenericSignatureMechanism):
    """
    An implementation of the RSA-SHA1 mechanism as described in
    draft-ietf-httpbis-message-signatures-01 section 5.1.2.2.

    This mechanism should not be used except for backwards compatibility
    with legacy code.  Additionally, the SHA-1 hash standard is known to
    be insecure.
    """
    padding_mechanism = padding.PKCS1v15
    hash_mechanism = hashes.SHA1


class Legacy_RSA_SHA256_Mechanism(GenericSignatureMechanism):
    """
    An implementation of the RSA-SHA256 mechanism as described in
    draft-ietf-httpbis-message-signatures-01 section 5.1.2.3.

    This mechanism should not be used except for backwards compatibility
    with legacy code.
    """
    padding_mechanism = padding.PKCS1v15
    hash_mechanism = hashes.SHA256


class Legacy_RSA_SHA512_Mechanism(GenericSignatureMechanism):
    """
    An implementation of the RSA-SHA512 mechanism as described in
    draft-ietf-httpbis-message-signatures-01 section 5.1.2.4.

    This mechanism should not be used except for backwards compatibility
    with legacy code.
    """
    padding_mechanism = padding.PKCS1v15
    hash_mechanism = hashes.SHA512


class HS2019_RSA_PSS_SHA512_Mechanism(GenericSignatureMechanism):
    """
    An implementation of the HS2019 mechanism for RSA keys, as described in
    draft-ietf-httpbis-message-signatures-01 section 5.1.2.1.
    """
    padding_mechanism = padding.PSS
    hash_mechanism = hashes.SHA512


class PipelineSignatureMechanism(HTTPSignatureMechanism):
    """
    A mechanism which acts as a verification pipeline for other mechanisms.
    At least one verify mechanism must be specified and only one signing mechanism
    may be specified.
    """
    verify_pipelines = []
    sign_mechanism = None

    def verify(self, pubkey: object, sigdata: bytes, sigstring: bytes, algorithm: str) -> bool:
        if not self.verify_pipelines:
            raise NotImplementedError()

        return True in [vp.verify(pubkey, sigdata, sigstring, algorithm) for vp in self.verify_pipelines]

    def sign(self, sigstring: bytes, privkey: object) -> str:
        if not self.sign_mechanism:
            raise NotImplementedError()

        return self.sign_mechanism.sign(sigstring, privkey)


class HS2019_RSA_Mechanism(PipelineSignatureMechanism):
    """
    A mechanism which tries the various RSA mechanisms and signs using RSASSA-PSS-SHA512.
    Use HS2019_RSA_Legacy_Mechanism if you need to sign using RSA-SHA256 signatures for
    ActivityPub compatibility.
    """
    verify_pipelines = [
        HS2019_RSA_PSS_SHA512_Mechanism(),
        Legacy_RSA_SHA512_Mechanism(),
        Legacy_RSA_SHA256_Mechanism(),
        Legacy_RSA_SHA1_Mechanism()
    ]
    sign_mechanism = HS2019_RSA_PSS_SHA512_Mechanism()


class HS2019_RSA_Legacy_Mechanism(HS2019_RSA_Mechanism):
    """
    A mechanism which uses the normal HS2019 RSA verification rules, but signs using
    RSA-SHA256 signatures for legacy ActivityPub compatibility.
    """
    sign_mechanism = Legacy_RSA_SHA256_Mechanism()


class HTTPSignatureVerifier(HTTPSignatureSigningStringMixIn):
    mechanism = HS2019_RSA_Legacy_Mechanism()

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

        return self.mechanism.verify(pubkey, sigdata, sigstring.encode('utf-8'), sig['algorithm'])


class HTTPLegacySignatureSigner(HTTPSignatureSigningStringMixIn):
    mechanism = HS2019_RSA_Legacy_Mechanism()

    def sign(self, headers: dict, key: object, key_id: str) -> dict:
        headers = {x.lower(): y for x, y in headers.items()}
        used_headers = headers.keys()

        # TODO: switch to hs2019 algorithm eventually...
        sig = {
            'keyId': key_id,
            'algorithm': 'rsa-sha256',
            'headers': ' '.join(used_headers)
        }

        sigstring = self.build_signing_string(headers, used_headers)
        sig['signature'] = self.mechanism.sign(sigstring.encode('utf-8'), key)

        chunks = ['{}="{}"'.format(k, v) for k, v in sig.items()]
        signed_headers = {'signature': ','.join(chunks)}

        headers.pop('(request-target)')
        headers.pop('host')

        signed_headers.update(headers)
        return signed_headers


# TODO: Implement new-style signatures as HTTPSignatureSigner.
HTTPSignatureSigner = HTTPLegacySignatureSigner
