from ... import app, __version__
from aiohttp.web import RouteTableDef, Response, json_response


routes = RouteTableDef()


@routes.post('/api/v1/statuses')
async def status_new(request):
    user = request['oauth_user']
    if not user:
        return json_response({'error': 'no oauth session found'}, status=400)

    post = await request.post()

    if not 'status' in post:
        return json_response({'error': 'post must have a status'}, status=400)

    create_activity = app.commonapi.post(user.actor(),
                                         spoiler_text=post.get('spoiler_text', None),
                                         status=post.get('status', None),
                                         content_type=post.get('content_type', 'text/plain'),
                                         visibility=post.get('visibility', 'public'))

    return json_response(create_activity.serialize_to_mastodon())


app.add_routes(routes)