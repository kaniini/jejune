from ..activity_streams import AS2Activity, registry


class Create(AS2Activity):
    __jsonld_type__ = 'Create'

    def mastodon_id(self):
        return self.child().mastodon_id()

registry.register_type(Create)