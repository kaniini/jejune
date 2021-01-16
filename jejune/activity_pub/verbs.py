from ..activity_streams import AS2Activity, registry


class Create(AS2Activity):
    __jsonld_type__ = 'Create'

registry.register_type(Create)