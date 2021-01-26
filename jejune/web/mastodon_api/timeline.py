import logging


from ... import app, __version__
from ...activity_streams.collection import AS2Collection
from ...activity_pub.actor import Actor

from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


# XXX: optimize
def render_timeline(request, items):
    serialized_items = [item.serialize_to_mastodon() for item in items if item]
    return json_response([si for si in serialized_items if si and 'error' not in si])


@routes.get('/api/v1/timelines/home')
async def home_timeline(request):
    user = request.get('oauth_user', None)
    if not user:
        return json_response({'error': 'no oauth session found'}, status=403)

    actor = user.actor()
    if not actor:
        return json_response({'error': 'bogus account - no AP actor found'}, status=500)

    limit = int(request.query.get('limit', 20))

    inbox_collection = AS2Collection.fetch_local(actor.inbox, use_pointers=True)
    items = inbox_collection.walk({'Create', 'Announce'}, limit,
                                  skip=0,
                                  max_id=request.query.get('max_id', None),
                                  since_id=request.query.get('since_id', None),
                                  min_id=request.query.get('min_id', None))

    return render_timeline(request, items)


@routes.get('/api/v1/timelines/public')
async def public_timeline(request):
    limit = int(request.query.get('limit', 20))
    deref_limit = app.max_timeline_length

    shared_inbox_collection = AS2Collection.fetch_local(app.shared_inbox_uri, use_pointers=True)
    deref_items = [ptr.dereference() for ptr in shared_inbox_collection.__items__[0:deref_limit]]

    return render_timeline(request, deref_items)


@routes.get('/api/v1/accounts/{id}/statuses')
async def user_timeline(request):
    req_user = request.get('oauth_user', None)
    if not req_user:
        return json_response({'error': 'no oauth session found'}, status=403)

    actor = Actor.fetch_from_hash(request.match_info['id'])
    if not actor:
        return json_response({'error': 'bogus account - no AP actor found'}, status=500)

    limit = int(request.query.get('limit', 20))
    deref_limit = app.max_timeline_length

    inbox_collection = await AS2Collection.fetch_from_uri(actor.outbox, use_pointers=True)
    if not inbox_collection:
        return json_response([])

    items = inbox_collection.walk({'Create', 'Announce'}, limit,
                                  skip=0,
                                  max_id=request.query.get('max_id', None),
                                  since_id=request.query.get('since_id', None),
                                  min_id=request.query.get('min_id', None))

    return render_timeline(request, items)


app.add_routes(routes)
