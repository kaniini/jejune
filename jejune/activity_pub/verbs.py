import logging


from ..activity_streams import AS2Activity, AS2Pointer, registry
from ..activity_streams.collection import AS2Collection


class Create(AS2Activity):
    __jsonld_type__ = 'Create'

    def mastodon_id(self):
        return self.child().mastodon_id()

registry.register_type(Create)


class Announce(AS2Activity):
    __jsonld_type__ = 'Announce'

    def mastodon_id(self):
        return '{0:d}.{1}'.format(int(self.published_ts()), self.storeIdentity)

    def serialize_to_mastodon(self):
        actor = AS2Pointer(self.actor).dereference()

        reblog = self.child().serialize_to_mastodon()
        reblog['account'] = actor.serialize_to_mastodon()
        reblog['id'] = self.mastodon_id()
        reblog['reblog'] = self.child().serialize_to_mastodon()

        return reblog

registry.register_type(Announce)


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

        if not object:
            logging.info('WTF: Accept Activity %r references child object %r which does not exist!',
                         self.id, self.object)
            return

        if not isinstance(object, AS2Activity):
            logging.info('WTF: Accept Activity %r references child object %r (%s) which does not have applicable side effects.',
                         self.id, object.id, object.type)
            return

        await object.accept_side_effects(self)
        await super().apply_side_effects()

registry.register_type(Accept)


class Reject(AS2Activity):
    __jsonld_type__ = 'Reject'
    __ephemeral__ = True

    async def apply_side_effects(self):
        object = self.child()

        if not object:
            logging.info('WTF: Accept Activity %r references child object %r which does not exist!',
                         self.id, self.object)
            return

        if not isinstance(object, AS2Activity):
            logging.info('WTF: Reject Activity %r references child object %r (%s) which does not have applicable side effects.',
                         self.id, object.id, object.type)
            return

        await object.reject_side_effects(self)
        await super().apply_side_effects()

registry.register_type(Reject)


class Follow(AS2Activity):
    __jsonld_type__ = 'Follow'
    __ephemeral__ = True

    async def apply_side_effects(self):
        followee = AS2Pointer(self.object).dereference()

        # XXX: implement blocks collection
        if not followee.manuallyApprovesFollowers:
            a = Accept(actor=followee.id, object=self.serialize(dict), to=[self.actor])
            await a.apply_side_effects()
        else:
            pass

    async def accept_side_effects(self, parent):
        followee = AS2Pointer(self.object).dereference()
        followee_collection = AS2Collection.fetch_local(followee.followers, use_pointers=True)
        followee_collection.prepend(AS2Pointer(self.actor))
        followee_collection.commit()

    async def reject_side_effects(self, parent):
        followee = AS2Pointer(self.object).dereference()
        followee_collection = AS2Collection.fetch_local(followee.followers, use_pointers=True)
        followee_collection.remove(AS2Pointer(self.actor))
        followee_collection.commit()

registry.register_type(Follow)


class Undo(AS2Activity):
    __jsonld_type__ = 'Undo'
    __ephemeral__ = True

    # XXX: actually implement
    async def apply_side_effects(self):
        pass
