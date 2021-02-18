import logging
import getpass


from jejune import app


def main():
    logging.info('Creating new user.')

    username = input('Username: ')
    password = getpass.getpass()
    display_name = input(f'Display name for {username}: ')
    email = input(f'E-mail address for {username}: ')
    bio = input(f'Bio for {username}: ')

    confirm = None
    while confirm not in ['y', 'n']:
        confirm = input(f'Going to create user "{username}".  Proceed? [y/n] ')

    if confirm == 'n':
        logging.info('Aborted user creation.')

    u = app.userapi.create_user(description=display_name,
                                actor_type='Person',
                                username=username,
                                email=email,
                                password=password,
                                bio=bio,
                                locked=False,
                                actor_uri=None)

    if not u:
        logging.info('Error creating user %r.', username)
        return

    logging.info('Created user %r as %r.', username, u.actor_uri)


if __name__ == '__main__':
    main()
