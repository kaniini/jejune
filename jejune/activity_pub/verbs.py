import logging


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

registry.register_type(Update)


class Accept(AS2Activity):
    __jsonld_type__ = 'Accept'
    __ephemeral__ = True

    async def apply_side_effects(self):
        object = self.child()

        if not isinstance(object, AS2Activity):
            logging.info('WTF: Accept Activity %r references child object %r (%s) which does not have applicable side effects.',
                         self.id, object.id, object.type)
            return

        await object.accept_side_effects()

registry.register_type(Accept)


class Reject(AS2Activity):
    __jsonld_type__ = 'Reject'
    __ephemeral__ = True

    async def apply_side_effects(self):
        object = self.child()

        if not isinstance(object, AS2Activity):
            logging.info('WTF: Reject Activity %r references child object %r (%s) which does not have applicable side effects.',
                         self.id, object.id, object.type)
            return

        await object.reject_side_effects()

registry.register_type(Reject)