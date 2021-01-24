from .. import app
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.post('/oauth/revoke')
@routes.post('/.well-known/jejune/oauth/revoke')
async def oauth_revoke(request):
    return json_response({})


@routes.post('/oauth/token')
@routes.post('/.well-known/jejune/oauth/token')
async def oauth_token(request):
    post = await request.post()

    if not 'username' in post:
        return json_response({'error': 'username is not provided'}, status=403)

    if not 'password' in post:
        return json_response({'error': 'password is not provided'}, status=403)

    u = app.userapi.find_user(post['username'])
    if not u:
        return json_response({'error': 'could not find account with this username and password'}, status=403)

    if not u.verify_password(post['password']):
        return json_response({'error': 'could not find account with this username and password'}, status=403)

    token = app.userapi.login(u)
    if not token:
        return json_response({'error': 'login failed due to internal error'}, status=500)

    return json_response(token.serialize(dict))


app.add_routes(routes)
