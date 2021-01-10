from ... import app
from aiohttp.web import RouteTableDef, json_response


routes = RouteTableDef()


@routes.get('/api/pleroma/frontend_configurations')
def frontend_configurations(request):
    return json_response(app.config['instance']['frontend-configurations'])


app.add_routes(routes)