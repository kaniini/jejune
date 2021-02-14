import logging


from ..activity_streams import AS2Activity, AS2Pointer, registry
from ..activity_streams.collection import AS2Collection


class Create(AS2Activity):
    __jsonld_type__ = 'Create'

    def mastodon_id(self):
        return self.child().mastodon_id()

    async def apply_side_effects(self):
        await super().apply_side_effects()

        child = self.child()
        if not child:
            return

        in_reply_to = getattr(child, 'inReplyTo', None)
        if not in_reply_to:
            return

        parent = AS2Pointer(in_reply_to).dereference()
        if not parent:
            return

        replies_collection_uri = getattr(parent, 'replies', None)
        if not replies_collection_uri:
            return

        replies_collection = AS2Collection.fetch_local(replies_collection_uri, use_pointers=True)
        if not isinstance(replies_collection, AS2Collection):
            return

        replies_collection.prepend(AS2Pointer(child.id))
        replies_collection.commit()

registry.register_type(Create)


# TODO: Add announce to an object's announces collection if one exists.
class Announce(AS2Activity):
    __jsonld_type__ = 'Announce'

    def mastodon_id(self):
        return '{0:d}.{1}'.format(int(self.published_ts()), self.storeIdentity)

    def serialize_to_mastodon(self):
        actor = AS2Pointer(self.actor).dereference()

        child = self.child()
        if not child:
            logging.info('WTF: Announce %r references non-existent child %r.', self.id, self.object)
            return None

        reblog = child.serialize_to_mastodon()
        reblog['account'] = actor.serialize_to_mastodon()
        reblog['id'] = self.mastodon_id()
        reblog['reblog'] = self.child().serialize_to_mastodon()

        return reblog

registry.register_type(Announce)


# TODO: Add likes to an object's likes collection if one exists.
class Like(AS2Activity):
    __jsonld_type__ = 'Like'

registry.register_type(Like)


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
        if not getattr(followee, 'manuallyApprovesFollowers', False) and followee.local():
            a = Accept(actor=followee.id, object=self.serialize(dict), to=[self.actor])
            await a.apply_side_effects()
        else:
            pass

        await super().apply_side_effects()

    async def accept_side_effects(self, parent):
        followee = AS2Pointer(self.object).dereference()
        followee_collection = AS2Collection.fetch_local(followee.followers, use_pointers=True)
        followee_collection.prepend(AS2Pointer(self.actor))
        followee_collection.commit()

        follower = AS2Pointer(self.actor).dereference()
        follower_collection = AS2Collection.fetch_local(follower.following, use_pointers=True)
        follower_collection.prepend(AS2Pointer(self.object))
        follower_collection.commit()

    async def reject_side_effects(self, parent):
        followee = AS2Pointer(self.object).dereference()
        followee_collection = AS2Collection.fetch_local(followee.followers, use_pointers=True)
        followee_collection.remove(AS2Pointer(self.actor))
        followee_collection.commit()

        follower = AS2Pointer(self.actor).dereference()
        follower_collection = AS2Collection.fetch_local(follower.following, use_pointers=True)
        follower_collection.remove(AS2Pointer(self.object))
        follower_collection.commit()

registry.register_type(Follow)


class Undo(AS2Activity):
    __jsonld_type__ = 'Undo'
    __ephemeral__ = True

    # XXX: actually implement
    async def apply_side_effects(self):
        pass
