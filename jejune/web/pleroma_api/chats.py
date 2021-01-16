from ... import app
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.get('/api/v1/pleroma/chats')
def chats(request):
    return json_response([])


app.add_routes(routes)