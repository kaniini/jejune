import aiohttp.web
import logging
import urllib.parse


from ..http_signatures import HTTPSignatureVerifier


class JejuneHTTPSignatureVerifier(HTTPSignatureVerifier):
    async def load_key(self, key_id: str) -> object:
        keyid_uri = urllib.parse.urlsplit(key_id)._replace(fragment='')
        if keyid_uri.path.endswith('/publickey'):
            keyid_uri = keyid_uri._replace(path=keyid_uri.path[0:-10])  # len('/publickey')

        from ..activity_streams import AS2Pointer
        actor_uri = AS2Pointer(urllib.parse.urlunsplit(keyid_uri)).serialize()

        from ..activity_pub.actor import Actor
        actor = await Actor.fetch_from_uri(actor_uri)
        if not actor:
            return None

        try:
            return self.load_pem_public_key(actor.publicKey['publicKeyPem'])
        except:
            return None


async def http_signatures_middleware(app, handler):
    verifier = JejuneHTTPSignatureVerifier()

    async def http_signatures_handler(request):
        request['validated'] = False

        if 'signature' in request.headers:
            request['validated'] = await verifier.validate(request)

            if not request['validated']:
                logging.info('HTTP Signature validation failed for: %s', data['actor'])
                return aiohttp.web.json_response({'error': 'signature check failed, signature did not match key'}, status=403)

        return (await handler(request))

    return http_signatures_handler
