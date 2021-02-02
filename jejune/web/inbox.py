import logging


from .. import app
from ..activity_streams.collection import AS2Collection, OrderedCollectionAdapter
from aiohttp.web import RouteTableDef, json_response, Response


routes = RouteTableDef()


@routes.post('/.well-known/jejune/inbox/{id}')
@routes.post('/.well-known/jejune/sharedinbox')
async def inbox_post(request):
    if not request['validated']:
        return json_response({'status': 'rejected; invalid signature'}, status=403)

    try:
        resp = await request.json()
        if not resp:
            return json_response({'status': 'rejected; malformed payload'}, status=406)

        app.inbox_processor.enqueue(resp)
    except:
        return json_response({'status': 'rejected; malformed payload'}, status=406)

    return json_response({'status': 'accepted'}, status=202)


@routes.get('/.well-known/jejune/inbox/{id}')
@routes.get('/.well-known/jejune/sharedinbox')
async def inbox_get(request):
    inbox_id = request.match_info.get('id', None)

    if inbox_id:
        u = request.get('oauth_user', None)
        if not u:
            return json_response({'status': 'unauthorized; matching oauth session token needed to read personal inboxes'}, status=403)

        a = u.actor()
        if not a:
            return json_response({'status': 'unauthorized; oauth session token is associated with non-existent actor'}, status=403)

        if not a.inbox.endswith(inbox_id):
            return json_response({'status': 'inbox capability URI does not match session token'}, status=403)

    rdf_uri = ''.join(['https://', app.hostname, request.path])
    logging.debug('ActivityPub: C2S: fetching inbox %r', rdf_uri)

    inbox_collection = await AS2Collection.fetch_from_uri(rdf_uri, use_pointers=True)
    adapter = OrderedCollectionAdapter(inbox_collection)

    return json_response(adapter.serialize(request))


app.add_routes(routes)
