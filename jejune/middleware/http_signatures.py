import aiohttp.web
import logging


from ..http_signatures import HTTPSignatureVerifier


async def http_signatures_middleware(app, handler):
    verifier = HTTPSignatureVerifier()

    async def http_signatures_handler(request):
        request['validated'] = False

        if 'signature' in request.headers and request.method == 'POST':
            data = await request.json()

            if 'actor' not in data:
                return aiohttp.web.json_response({'error': 'signature check failed, no actor in message'}, status=403)

            if not (await verifier.validate(data['actor'], request)):
                logging.info('HTTP Signature validation failed for: %s', data['actor'])
                return aiohttp.web.json_response({'error': 'signature check failed, signature did not match key'}, status=403)

        return (await handler(request))

    return http_signatures_handler
