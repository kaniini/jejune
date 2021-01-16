from . import AS2Object, registry


class Note(AS2Object):
    __jsonld_type__ = 'Note'

registry.register_type(Note)