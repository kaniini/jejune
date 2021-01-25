import jinja2
import logging
import re

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


if not outbox and featured_user:
    outbox = getattr(featured_user, 'outbox', None)


logging.info('Simple Frontend: Using outbox %r.', outbox)


jinja_env.globals['featured_user'] = featured_user


from jejune.activity_streams import AS2Object


class SimpleFrontendSupport:
    stemming_regex = re.compile(r'[^a-zA-Z0-9\s]')

    def stem(self, object: AS2Object) -> str:
        payload = getattr(object, 'name', None)
        if not payload:
            payload = getattr(object, 'summary', None)
        if not payload:
            payload = getattr(object, 'source', {}).get('content', None)

        if not payload:
            return 'unknown'

        payload = self.stemming_regex.sub('', payload)

        return '-'.join(payload.lower().split()[0:10])

    def friendly_uri(self, object: AS2Object) -> str:
        if not object.local():
            return object.id

        if object.type not in ['Note', 'Article', 'Image']:
            return object.id

        stem = self.stem(object)
        return f'https://{app.hostname}/activity/{object.storeIdentity}/{stem}'


app.frontend_support = SimpleFrontendSupport()
