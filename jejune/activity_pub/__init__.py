from ..activity_streams import AS2Object
from .actor import Person, Group, Organization, Application, Service


AP_TYPES = {
    'Person': Person,
    'Group': Group,
    'Organization': Organization,
    'Application': Application,
    'Service': Service,
}


def deserialize_from_ap(data: dict) -> AS2Object:
    if data['type'] in AP_TYPES:
        return AP_TYPES[data['type']].deserialize_from_json(data)

    return None