import logging
import jinja2

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader('jejune.plugin.web.simple_frontend', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml']),
)


from jejune import app
jinja_env.globals['app'] = app


from . import routes


config = app.config['instance'].get('frontend-configurations', {}).get('simple-frontend')
outbox = config.get('outbox', None)
featured_user = app.userapi.find_user(config.get('user', None)).actor()


logging.info('Simple Frontend: Config: %r', config)


if not outbox:
    outbox = getattr(featured_user, 'outbox', None)


logging.info('Simple Frontend: Using outbox %r.', outbox)
