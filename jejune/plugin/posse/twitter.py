import logging


from jejune import app


def get_twitter_config() -> dict:
    return app.config.get('raw', {}).get('twitter', {})


def preflight() -> bool:
    cfg = get_twitter_config()
    if not cfg:
        return False
    required_keys = ['consumer-key', 'consumer-secret', 'access-token', 'access-secret', 'users']
    present = [k in cfg.keys() for k in required_keys]
    return False not in present


if preflight():
    pass
else:
    logging.info('POSSE to Twitter: Preflight checks failed; make sure valid consumer and access tokens and secrets are configured!')
