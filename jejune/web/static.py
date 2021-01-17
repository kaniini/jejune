from .. import app

from aiohttp.web import FileResponse


async def index_html(request):
    return FileResponse(path=app.config['paths']['static'] + '/index.html')


app.router.add_get('/.well-known/jejune', index_html)
app.router.add_static('/static', path=app.config['paths']['static'] + '/static', name='static')
app.router.add_static('/.well-known/jejune/upload', path=app.config['paths']['upload'], name='upload')