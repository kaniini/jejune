import uuid


from jejune import get_jejune_app


def create_user(actor_type='Person'):
    app = get_jejune_app()

    return app.userapi.create_user(str(uuid.uuid4()),
                                   actor_type,
                                   str(uuid.uuid4()),
                                   'test@test.com',
                                   None,
                                   'test user',
                                   False)