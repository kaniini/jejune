import aiohttp
import logging


from async_timeout import timeout
from .activity_pub.actor import Actor


class WebfingerClient:
    def __init__(self, app):
        self.app = app

    async def finger(self, domain: str, resource: str) -> dict:
        async with timeout(5):
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://{domain}/.well-known/webfinger',
                                       params={'resource': resource}) as resp:
                    return (await resp.json())

        return {}

    async def discover_actor(self, username: str) -> Actor:
        domain = username.split('@', 2)[1]

        webfinger_data = await self.finger(domain, f'acct:{username}')

        for link in webfinger_data['links']:
            if link.get('rel', None) != 'self':
                continue

            if link.get('type', None) == 'application/activity+json':
                logging.debug('Discovered %r as actor %r.', username, link.get('href'))
                return (await Actor.fetch_from_uri(link.get('href')))