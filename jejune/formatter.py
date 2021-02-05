import logging
import markdown
import re


MENTIONS_RE = re.compile(r'\B(@[a-zA-Z0-9@\.]*)\s*')


class Formatter:
    def __init__(self, app):
        self.app = app

    def tokenize_mentions(self, message: str) -> list:
        return [token for token in MENTIONS_RE.split(message) if token]

    async def replace_mentions(self, message: str) -> [str, list]:
        tokens = self.tokenize_mentions(message)
        new_tokens = []
        mentions = []

        for token in tokens:
            logging.debug('Formatter: processing token %r for mentions.', token)

            if token[0] == '@':
                mention = token[1:]

                u = await self.app.userapi.discover_user(mention)
                if not u:
                    new_tokens += [token]
                    continue

                actor = u.actor()
                if not actor:
                    new_tokens += [token]
                    continue

                user_uri = getattr(actor, 'uri', actor.id)
                token = f'<span class="h-card"><a href="{user_uri}" class="u-url mention" rel="ugc">@{actor.preferredUsername}</a></span> '
                new_tokens += [token]
                mentions += [actor]
            else:
                new_tokens += [token]

        return (''.join(new_tokens), mentions)

    def replace_hashtags(self, message: str) -> [str, list]:
        return (message, [])

    async def format(self, message: str, content_type: str) -> [str, list]:
        orig_message = message

        try:
            message, mentions = await self.replace_mentions(message)
            message, hashtags = self.replace_hashtags(message)
            message = markdown.markdown(message)
        except Exception as e:
            logging.exception('Formatter: Encountered %r while formatting %r.', e, message) 
            return (orig_message, [])

        return (message, mentions)
