from .. import app, __version__
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


def upload_limits():
    return {'avatar': app.config['instance']['limits']['avatar-size'],
            'background': app.config['instance']['limits']['background-size'],
            'banner': app.config['instance']['limits']['banner-size'],
            'general': app.config['instance']['limits']['general-upload-size']}


@routes.get('/.well-known/nodeinfo')
def nodeinfo_links(request):
    links = [
        {'rel': 'http://nodeinfo.diaspora.software/ns/schema/2.0',
         'href': 'https://{0}/.well-known/nodeinfo/2.0.json'.format(app.config['instance']['hostname'])},
        {'rel': 'http://nodeinfo.diaspora.software/ns/schema/2.1',
         'href': 'https://{0}/.well-known/nodeinfo/2.1.json'.format(app.config['instance']['hostname'])},
    ]
    return json_response({'links': links})


# XXX: would be nice to get Pleroma FE to look up the actual URIs.
@routes.get('/.well-known/nodeinfo/{version}.json')
@routes.get('/nodeinfo/{version}.json')
def nodeinfo_response(request):
    data = {
        'metadata': {
             'nodeDescription': app.config['instance'].get('description'),
             'nodeName': app.config['instance'].get('name'),
             'uploadLimits': upload_limits(),
        },
        'openRegistrations': app.config['instance'].get('registrations', False),
        'protocols': [
             'activitypub',
        ],
        'services': {
             'inbound': [],
             'outbound': [],
        },
        'software': {
             'name': 'jejune',
             'repository': 'https://github.com/kaniini/jejune',
             'version': __version__,
        },
        'version': request.match_info['version'],
    }
    return json_response(data)


app.add_routes(routes)