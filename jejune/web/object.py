from . import fetch_request_data

from .. import app
from aiohttp.web import RouteTableDef, json_response, Response


routes = RouteTableDef()


@routes.get('/.well-known/jejune/object/{uuid}')
async def object(request):
     uri = app.object_uri_for(request.match_info['uuid'], 'object')
     if not app.rdf_store.local_uri_exists(uri):
         return json_response({'error': 'object not found'}, status=404)

     (object, mtime) = app.rdf_store.fetch_cached(uri)
     return Response(text=object, content_type='application/activity+json')


@routes.get('/.well-known/jejune/actor')
async def instance_actor(request):
     uri = app.make_well_known_uri('actor')
     if not app.rdf_store.local_uri_exists(uri):
         return json_response({'error': 'object not found'}, status=404)

     (object, mtime) = app.rdf_store.fetch_cached(uri)
     return Response(text=object, content_type='application/activity+json')


@routes.post('/.well-known/jejune/object-proxy')
async def object_proxy(request):
     u = request.get('oauth_user', None)
     if not u:
         return json_response({'status': 'unauthorized; valid oauth session token needed to use object proxy'}, status=403)

     rdata = await fetch_request_data(request)
     if 'id' not in rdata.keys():
         return json_response({'status': 'invalid request; missing id parameter'}, status=500)

     object = await app.rdf_store.fetch(rdata['id'])
     if not object:
         return json_response({'error': 'object not found'}, status=404)

     return Response(text=object, content_type='application/activity+json')


app.add_routes(routes)
