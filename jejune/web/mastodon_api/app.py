from ... import app, __version__
from aiohttp.web import RouteTableDef, Response


routes = RouteTableDef()


@routes.post('/api/v1/apps')
async def new_app(request):
    post = await request.post()

    obj = app.userapi.create_app(post.get('client_name'),
                                 post.get('redirect_uris'),
                                 post.get('website'))
    return Response(text=obj.serialize(), content_type='application/json')


app.add_routes(routes)