from .. import app
from aiohttp.web import RouteTableDef, json_response, Response


routes = RouteTableDef()


@routes.get('/.well-known/jejune/object/{uuid}')
async def object(request):
     uri = app.rdf_object_uri_for(request.match_info['uuid'])
     if not app.rdf_store.local_uri_exists(uri):
         return json_response({'error': 'object not found'}, status=404)

     (object, mtime) = app.rdf_store.fetch_cached(uri)
     return Response(text=object, content_type='application/activity+json')


app.add_routes(routes)