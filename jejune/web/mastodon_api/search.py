import logging


from ... import app, __version__
from ...activity_streams.collection import AS2Collection

from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


# XXX: actually implement a search engine (this will need some design consideration),
@routes.get('/api/v1/search')
@routes.get('/api/v2/search')
async def search(request):
    query = request.query.get('q', '')

    accounts = []

    # we don't let anonymous users do search queries
    if request['oauth_user']:
        actor = await app.userapi.discover_user(query)
        if actor:
            accounts += [actor.serialize_to_mastodon()]

    statuses = []
    hashtags = []

    return json_response({'accounts': accounts, 'statuses': statuses, 'hashtags': hashtags})


app.add_routes(routes)