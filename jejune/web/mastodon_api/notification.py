from ... import app, __version__
from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


@routes.get('/api/v1/notifications')
def notifications_get(request):
    return json_response([])


app.add_routes(routes)