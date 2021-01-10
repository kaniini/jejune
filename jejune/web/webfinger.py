from .. import app
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.get('/.well-known/webfinger')
async def webfinger(request):
    resource = request.query['resource']

    if not resource.endswith(app.config['instance']['hostname']):
        return json_response({'error': 'user not found'}, status=404)

    username = resource.split('@')[0][5:]
    user = app.userapi.find_user(username)
    if not user:
        return json_response({'error': 'user not found'}, status=404)

    data = {
        "aliases": [user.actor_uri],
        "links": [
             {"href": user.actor_uri, "rel": "self", "type": "application/activity+json"},
             {"href": user.actor_uri, "rel": "self", "type": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'},
        ],
        "subject": resource,
    }

    return json_response(data)


app.add_routes(routes)