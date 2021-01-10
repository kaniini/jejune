from ... import app, __version__
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.get('/api/v1/instance')
def instance(request):
    data = {
        'approval_required': False,
        'avatar_upload_limit': app.config['instance']['limits']['avatar-size'],
        'background_upload_limit': app.config['instance']['limits']['background-size'],
        'banner_upload_limit': app.config['instance']['limits']['banner-size'],
        'upload_limit': app.config['instance']['limits']['general-upload-size'],
        'registrations': app.config['instance']['registrations'],
        'title': app.config['instance']['name'],
        'version': '2.7.2 (compatible; Jejune {0})'.format(__version__),
    }
    return json_response(data)


app.add_routes(routes)