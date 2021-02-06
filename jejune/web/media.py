import logging


from .. import app, __version__
from ..activity_streams.collection import AS2Collection

from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


@routes.post('/.well-known/jejune/media')
async def upload_media(request):
    user = request['oauth_user']
    if not user:
        return json_response({'error': 'no oauth session found'}, status=400)

    reader = await request.multipart()
    while True:
        part = await reader.next()

        if not part:
            break

        if part.filename:
            data = await part.read(decode=False)
            filename = part.filename
            attachment = app.commonapi.upload_media(user.actor(), data, filename, part.headers['Content-Type'])

            return json_response(attachment.serialize(dict))

    return json_response({'error': 'media not found'}, status=500)

app.add_routes(routes)
