import logging


from .. import app, __version__
from ..activity_streams import AS2_CONTEXT

from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


@routes.get('/.well-known/jejune/search')
async def search(request):
    user = request['oauth_user']
    if not user:
        return json_response({'error': 'no oauth session found'}, status=400)

    query = request.query.get('q', None)
    items = []

    if query and '@' in query:
        qu = await app.userapi.discover_user(query)
        if qu:
            actor = qu.actor()
            items += [actor.serialize(dict)]

    message = {
        '@context': AS2_CONTEXT,
        'type': 'Collection',
        'items': items,
        'totalItems': len(items),
    }

    return json_response(message)

app.add_routes(routes)
