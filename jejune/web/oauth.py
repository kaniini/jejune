import logging


from . import jinja_env, fetch_request_data
from .. import app
from aiohttp.web import RouteTableDef, Response, json_response, HTTPFound


routes = RouteTableDef()


@routes.post('/oauth/revoke')
@routes.post('/.well-known/jejune/oauth/revoke')
async def oauth_revoke(request):
    return json_response({})


@routes.post('/oauth/token')
@routes.post('/.well-known/jejune/oauth/token')
async def oauth_token(request):
    post = await fetch_request_data(request)

    if post['grant_type'] == 'password':
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
    elif post['grant_type'] == 'authorization_code':
        token = app.userapi.find_token(post['code'])
        if not token:
            return json_response({'error': 'invalid token'}, status=403)

        return json_response(token.serialize(dict))


@routes.get('/oauth/authorize')
@routes.get('/.well-known/jejune/oauth/authorize')
async def oauth_authorize(request):
    client_id = request.query.get('client_id')
    redirect_uri = request.query.get('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob')

    client_app = app.userapi.find_app(client_id)
    if not client_app:
        return json_response({'error': 'application not found'}, status=403)

    template = jinja_env.get_template('oauth-login.html')
    return Response(text=template.render(client_app=client_app, redirect_uri=redirect_uri),
                    content_type='text/html')


@routes.post('/oauth/authorize')
@routes.post('/.well-known/jejune/oauth/authorize')
async def oauth_authorize_post(request):
    post = await request.post()

    client_id = post.get('client_id', None)
    redirect_uri = post.get('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob')

    def handle_error(error):
        template = jinja_env.get_template('oauth-login.html')
        return Response(text=template.render(client_app=client_app, redirect_uri=redirect_uri, error=error),
                        content_type='text/html')

    u = app.userapi.find_user(post['username'])
    if not u:
        return handle_error('could not find account with this username and password')

    if not u.verify_password(post['password']):
        return handle_error('could not find account with this username and password')

    token = app.userapi.login(u)
    if not token:
        return handle_error('login failed due to internal error')

    if redirect_uri == 'urn:ietf:wg:oauth:2.0:oob':
        template = jinja_env.get_template('oauth-oob.html')
        return Response(text=template.render(access_token=token.access_token), content_type='text/html')

    final_uri = redirect_uri + f'?code={token.access_token}'
    raise HTTPFound(final_uri)


app.add_routes(routes)
