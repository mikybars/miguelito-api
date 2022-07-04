import logging
import re
import string
from itertools import chain
from os import environ as env
from random import choice

import src.repo as repo
from src.validators import url as is_valid_url


LOGLEVEL = env.get('LOGLEVEL', 'WARN').upper()
root_logger = logging.getLogger()
handler = root_logger.handlers[0]
root_logger.setLevel(LOGLEVEL)
handler.setFormatter(logging.Formatter('[%(levelname)-8s] %(message)s'))


def generate_path(len):
    new_path = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
    if repo.is_taken(new_path):
        return generate_path(len)
    return new_path


def validate_url(url):
    if not is_valid_url(url):
        raise Exception("URL is invalid")


def validate_custom_path(path):
    if not path:
        return

    path_format = "^[A-Za-z0-9_-]*$"
    if not re.match(path_format, path):
        raise Exception(f"Path does not match regex {path_format}")

    if repo.is_taken(path):
        raise Exception("Path is already in use")


def shorten_url(event, context):
    if 'custom_path' in event:
        url, path, user = [v.strip() for v in event.values()]
    else:
        url, = [v.strip() for v in event.values()]
        path = None
        user = None

    validate_url(url)
    validate_custom_path(path)

    if not path:
        path = generate_path(len=7)

    return repo.save(path, url, user)


def list_urls(event, context):
    user, = event.values()

    return repo.find_by_user(user)


def delete_url(event, context):
    path, user = event.values()

    try:
        repo.delete(path=path, user=user)
    except repo.PathAndUserNotFound:
        raise Exception('forbidden')


def edit_url(event, context):
    path, user, data = event.values()
    if 'path' in data:
        validate_custom_path(data['path'])
    if 'origin' in data:
        validate_url(data['origin'])
    try:
        repo.update(path=path, user=user, data=data)
    except repo.PathAndUserNotFound:
        raise Exception('forbidden')
