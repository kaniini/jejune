import logging


from . import jinja_env
from jejune import app
from jejune.activity_streams import AS2Object, AS2Pointer
from jejune.activity_streams.collection import AS2Collection
from aiohttp.web import RouteTableDef, Response, json_response, HTTPFound


routes = RouteTableDef()


@routes.get('/')
@routes.get('/page/{page}')
async def index(request):
    from . import outbox

    page = int(request.match_info.get('page', 1))
    activities_per_page = 20
    skip = (page - 1) * activities_per_page

    activities = []

    if outbox:
        coll = AS2Collection.fetch_local(outbox, use_pointers=True)
        if coll:
            activities = coll.walk({'Create', 'Announce'}, activities_per_page, skip=skip)

    template = jinja_env.get_template('index.html')

    return Response(text=template.render(activities=activities), content_type='text/html')


@routes.get('/activity/{hash}/{stem}')
async def activity(request):
    activity = AS2Object.fetch_from_hash(request.match_info['hash'])
    if not activity:
        return Response(text='activity not found', status=404)

    if request.headers.get('Accept', 'text/html') in ['application/activity+json', 'application/ld+json']:
        return json_response(activity.serialize(dict), content_type='application/activity+json')

    template = jinja_env.get_template('activity-view.html')

    return Response(text=template.render(activity=activity, replies=[]), content_type='text/html')


app.add_routes(routes)
app.router.add_static('/frontend', path=app.config['paths']['static'] + '/frontend', name='frontend')
