import logging


from .. import app
from ..activity_streams.collection import AS2Collection, OrderedCollectionAdapter
from aiohttp.web import RouteTableDef, json_response, Response


routes = RouteTableDef()


@routes.get('/.well-known/jejune/collection/{id}')
async def collection_get(request):
    collection_id = request.match_info.get('id', None)

    if not collection_id:
        return json_response({'status': 'invalid capability URI'}, status=403)

    rdf_uri = ''.join(['https://', app.hostname, request.path])
    logging.debug('ActivityPub: C2S: fetching collection %r', rdf_uri)

    collection = await AS2Collection.fetch_from_uri(rdf_uri, use_pointers=True)
    adapter = OrderedCollectionAdapter(collection)

    return json_response(adapter.serialize(request))


app.add_routes(routes)
