from ..activity_streams import AS2Activity, registry


class Create(AS2Activity):
    __jsonld_type__ = 'Create'

    def mastodon_id(self):
        return self.child().mastodon_id()

registry.register_type(Create)


class Update(AS2Activity):
    __jsonld_type__ = 'Update'
    __ephemeral__ = True

    async def apply_side_effects(self):
        if self.local():
            return

        object = self.child()

        for k, v in self.object.items():
            setattr(object, k, v)

        object.commit()