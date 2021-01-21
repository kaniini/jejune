from .. import app
from aiohttp.web import RouteTableDef, json_response, Response


routes = RouteTableDef()


@routes.post('/.well-known/jejune/inbox/{id}')
@routes.post('/.well-known/jejune/sharedinbox')
async def inbox(request):
    if not request['validated']:
        return json_response({'status': 'rejected; invalid signature'}, status=403)

    try:
        resp = await request.json()
        if not resp:
            return json_response({'status': 'rejected; malformed payload'}, status=406)

        app.inbox_processor.enqueue(resp)
    except:
        return json_response({'status': 'rejected; malformed payload'}, status=406)

    return json_response({'status': 'accepted'}, status=202)


app.add_routes(routes)