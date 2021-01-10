import logging


async def oauth_middleware(app, handler):
    async def oauth_handler(request):
        if 'authorization' in request.headers:
            access_token = request.headers['authorization'].split(' ')[-1]
            request['oauth_user'] = app.userapi.find_login_from_token(access_token)

        return (await handler(request))

    return oauth_handler