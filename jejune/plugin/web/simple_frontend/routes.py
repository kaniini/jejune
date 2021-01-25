import logging


from . import jinja_env
from jejune import app
from jejune.activity_streams import AS2Object, AS2Pointer
from aiohttp.web import RouteTableDef, Response, json_response, HTTPFound


routes = RouteTableDef()


@routes.get('/')
async def index(request):
    from . import outbox, featured_user

    activities = []

    if outbox:
        coll = AS2Pointer(outbox).dereference()
        activities = [act for act in coll.__items__ if act.type in ['Create', 'Announce', 'Like']]

    template = jinja_env.get_template('index.html')

    return Response(text=template.render(activities=activities, featured_user=featured_user), content_type='text/html')


app.add_routes(routes)
app.router.add_static('/frontend', path=app.config['paths']['static'] + '/frontend', name='frontend')
