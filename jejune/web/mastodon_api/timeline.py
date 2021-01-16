from ... import app, __version__
from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


@routes.get('/api/v1/timelines/home')
def home_timeline(request):
    items = []

    return json_response([item.serialize_to_mastodon() for item in items])


@routes.get('/api/v1/timelines/public')
def public_timeline(request):
    items = []

    return json_response([item.serialize_to_mastodon() for item in items])


app.add_routes(routes)