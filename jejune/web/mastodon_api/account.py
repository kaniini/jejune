import logging


from ... import app
from aiohttp.web import RouteTableDef, json_response


from ...activity_pub.actor import Actor


routes = RouteTableDef()


@routes.post('/api/v1/accounts')
async def new_accounts(request):
    if not app.config['instance']['registrations']:
        return json_response({'error': 'registrations are not allowed'}, status=403)

    post = await request.json()

    if 'fullname' not in post.keys():
        return json_response({'error': 'missing display name'}, status=400)

    if 'username' not in post.keys():
        return json_response({'error': 'missing username'}, status=400)

    if 'email' not in post.keys():
        return json_response({'error': 'missing email'}, status=400)

    if 'password' not in post.keys():
        return json_response({'error': 'missing password'}, status=400)

    obj = app.userapi.create_user(post.get('fullname'),
                                  post.get('actortype', 'Person'),
                                  post.get('username'),
                                  post.get('email'),
                                  post.get('password'),
                                  post.get('bio'),
                                  False)

    token = app.userapi.login(obj)

    return json_response(token.serialize(dict))


@routes.get('/api/v1/accounts/verify_credentials')
async def verify_credentials(request):
    if not request['oauth_user']:
        return json_response({'error': 'no oauth session found'}, status=400)

    return json_response(request['oauth_user'].serialize_to_mastodon())


@routes.post('/api/v1/accounts/update_credentials')
@routes.patch('/api/v1/accounts/update_credentials')
async def update_credentials(request):
    if not request['oauth_user']:
        return json_response({'error': 'no oauth session found'}, status=400)

    reader = await request.multipart()
    while True:
        part = await reader.next()
        if not part:
            break

        if 'avatar' in part.headers['Content-Disposition']:
            data = await part.read(decode=False)
            app.userapi.update_avatar(request['oauth_user'], data, part.headers['Content-Type'])

    return json_response(request['oauth_user'].serialize_to_mastodon())


@routes.post('/api/v1/accounts/{id}/follow')
async def follow(request):
    user = request['oauth_user']

    if not user:
        return json_response({'error': 'no oauth session found'}, status=400)

    follower = user.actor()
    followee = Actor.fetch_from_hash(request.match_info['id'])
    if not followee:
        return json_response({'error': 'account not found'}, status=404)

    app.userapi.follow(follower, followee)

    return json_response(follower.mastodon_relationships_with(followee))


@routes.post('/api/v1/accounts/{id}/unfollow')
async def unfollow(request):
    user = request['oauth_user']

    if not user:
        return json_response({'error': 'no oauth session found'}, status=400)

    follower = user.actor()
    followee = Actor.fetch_from_hash(request.match_info['id'])
    if not followee:
        return json_response({'error': 'account not found'}, status=404)

    app.userapi.unfollow(follower, followee)

    return json_response(follower.mastodon_relationships_with(followee))


app.add_routes(routes)
