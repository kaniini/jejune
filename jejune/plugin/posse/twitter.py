import asyncio
import logging


from jejune import app
from jejune.activity_streams import AS2Object
from peony import PeonyClient


def get_twitter_config() -> dict:
    return app.config.get('raw', {}).get('twitter', {})


def preflight() -> bool:
    cfg = get_twitter_config()
    if not cfg:
        return False
    required_keys = ['consumer-key', 'consumer-secret', 'access-token', 'access-secret', 'users']
    present = [k in cfg.keys() for k in required_keys]
    return False not in present


client = None


def stemmer(msg):
    chopped = msg[0:240]
    if chopped[-1] in {'.', '?', '!'}:
        return chopped

    chopped, _ = chopped.rsplit(None, 1)
    return ''.join([chopped, '…'])


async def listener(uri: str, activity: AS2Object):
    logging.debug('POSSE to Twitter: Listener was called!')

    if activity.type != 'Create':
        return

    child = activity.child()
    if not child:
        return

    # get the markdown source
    source = getattr(child, 'summary', None)
    if not source:
        source = getattr(child, 'source', {}).get('content', None)
    if not source:
        return

    logging.debug('POSSE to Twitter: Attempting to POSSE object %r to Twitter [%s].', child.id, source)

    # trim the source text down so it will fit in a tweet (240 chars, allowing 40 for the shortlink)
    stem = stemmer(source)
    final_status = ' '.join([stem, child.url])

    # upload media
    attachments = getattr(child, 'attachment', [])
    uris = [attachment['url'] for attachment in attachments if 'url' in attachment.keys()]
    upload_tasks = [client.upload_media(uri) for uri in uris]

#    medias = await asyncio.gather(*upload_tasks)
    medias = []
    result = await client.api.statuses.update.post(status=final_status,
                                                   media_ids=[media.media_id for media in medias])

    logging.debug('POSSE to Twitter: got %r from API', result)


if preflight():
    cfg = get_twitter_config()

    client = PeonyClient(consumer_key=cfg['consumer-key'],
                         consumer_secret=cfg['consumer-secret'],
                         access_token=cfg['access-token'],
                         access_token_secret=cfg['access-secret'])

    for user in cfg['users']:
        u = app.userapi.find_user(user)
        if not u:
            logging.info('POSSE to Twitter: Attempting to POSSE for non-existent account %r.', user)
            continue

        a = u.actor()
        if not a:
            logging.info('POSSE to Twitter: Attempting to POSSE for non-existent actor belonging to account %r.', user)
            continue

        logging.info('POSSE to Twitter: Setting up listener for outbox %r.', a.outbox)
        app.publisher.attach_uri_listener(a.outbox, listener)
else:
    logging.info('POSSE to Twitter: Preflight checks failed; make sure valid consumer and access tokens and secrets are configured!')
