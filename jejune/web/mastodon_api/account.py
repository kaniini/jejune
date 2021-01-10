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

    return json_response(token.serialize())


app.add_routes(routes)