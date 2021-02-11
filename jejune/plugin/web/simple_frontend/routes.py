import logging
import base62


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

    coll_size = 0
    if outbox:
        coll = AS2Collection.fetch_local(outbox, use_pointers=True)
        if coll:
            coll_size = len(coll)
            activities = coll.walk({'Create', 'Announce'}, activities_per_page, skip=skip)

    total_pages = 0
    if coll_size:
        total_pages = int(coll_size / activities_per_page)

    template = jinja_env.get_template('index.html')

    return Response(text=template.render(activities=activities,
                                         page=page,
                                         total_pages=total_pages),
                    content_type='text/html')


@routes.get('/feed.atom')
async def feed(request):
    from . import outbox

    activities_per_page = 20
    activities = []

    if outbox:
        coll = AS2Collection.fetch_local(outbox, use_pointers=True)
        if coll:
            activities = coll.walk({'Create', 'Announce'}, activities_per_page)

    template = jinja_env.get_template('feed.xml')
    return Response(text=template.render(activities=list(activities)), content_type='application/atom+xml')


@routes.get('/activity/{hash}/{stem}')
async def activity(request):
    hash = request.match_info['hash']
    if not len(hash) == 64:
        inthash = base62.decode(hash)
        hash = hex(inthash)[2:]

        if len(hash) % 2 == 1:
            hash = '0' + hash

    activity = AS2Object.fetch_from_hash(hash)
    if not activity:
        return Response(text='activity not found', status=404)

    # TODO: Make this a function somewhere.
    accept_types = request.headers.get('Accept', 'text/html').split(',')
    accept_prefs = []
    for accept_type in accept_types:
        accept_type = accept_type.strip()
        frags = accept_type.split(';')
        q = 1.0

        props = {}
        for frag in frags[1:]:
            k, _, v = frag.partition('=')
            props[k] = v

        if 'q' in props.keys():
            q = float(props['q'])

        accept_prefs += [[frags[0], q]]

    sorted_prefs = sorted(accept_prefs, key=lambda x: x[1], reverse=True)

    if sorted_prefs[0][0] in ['application/activity+json', 'application/ld+json']:
        return json_response(activity.serialize(dict), content_type='application/activity+json')

    template = jinja_env.get_template('activity-view.html')

    return Response(text=template.render(activity=activity, replies=[]), content_type='text/html')


@routes.get('/l/{hash}')
async def shortlink(request):
    hash = request.match_info['hash']
    if not len(hash) == 64:
        inthash = base62.decode(hash)
        hash = hex(inthash)[2:]

        if len(hash) % 2 == 1:
            hash = '0' + hash

    activity = AS2Object.fetch_from_hash(hash)
    if not activity:
        return Response(text='activity not found', status=404)

    raise HTTPFound(activity.url)


app.add_routes(routes)
app.router.add_static('/frontend', path=app.config['paths']['static'] + '/frontend', name='frontend')
