import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader('jejune.web', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml']),
)


from .. import app
jinja_env.globals['app'] = app


from . import object
from . import webfinger
from . import nodeinfo
from . import mastodon_api
from . import pleroma_api
from . import static
from . import inbox
from . import oauth
