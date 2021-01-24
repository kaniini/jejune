import yaml


def get_paths(yaml_file: dict) -> dict:
    paths = yaml_file.get('paths', dict())

    return {
        'rdf': paths.get('rdf', 'store/rdf'),
        'userdb': paths.get('userdb', 'store/userdb'),
        'static': paths.get('static', 'static'),
        'upload': paths.get('upload', 'store/upload'),
    }


def get_listener(yaml_file: dict) -> dict:
    listener = yaml_file.get('listener', dict())

    return {
        'bind': listener.get('bind', '127.0.0.1'),
        'port': listener.get('port', 8080)
    }


def get_limits(limits: dict) -> dict:
    return {
        'post-chars': limits.get('post-chars', 5000),
        'avatar-size': limits.get('avatar-size', 2000000),
        'background-size': limits.get('background-size', 4000000),
        'banner-size': limits.get('banner-size', 4000000),
        'general-upload-size': limits.get('general-upload-size', 16000000),
        'timeline-length': limits.get('timeline-length', 4096),
    }


def get_instance(yaml_file: dict) -> dict:
    instance = yaml_file.get('instance', dict())

    return {
        'name': instance.get('name', 'A Misconfigured Jejune Instance'),
        'hostname': instance.get('hostname', 'misconfigured.example'),
        'frontend-configurations': instance.get('frontend-configurations', dict()),
        'limits': get_limits(instance.get('limits', dict())),
        'registrations': instance.get('registrations', False),
        'plugins': instance.get('plugins', []),
    }


def get_federation(yaml_file: dict) -> dict:
    federation = yaml_file.get('federation', dict())

    return {
        'enabled': federation.get('enabled', True),
    }


def load_config(path='jejune.yaml') -> dict:
    with open(path) as f:
        options = {}

        ## Prevent a warning message for pyyaml 5.1+
        if getattr(yaml, 'FullLoader', None):
            options['Loader'] = yaml.FullLoader

        yaml_file = yaml.load(f, **options)

        config = {
            'paths': get_paths(yaml_file),
            'listener': get_listener(yaml_file),
            'instance': get_instance(yaml_file),
            'federation': get_federation(yaml_file),
        }
        return config
