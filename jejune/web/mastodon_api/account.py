from ... import app
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.post('/api/v1/accounts')
async def new_accounts(request):
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


app.add_routes(routes)