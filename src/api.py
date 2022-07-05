import logging
import re
import string
import src.repo as repo
from itertools import chain
from os import environ as env
from random import choice

from src.shorturl import ShortUrl
from src.validators import url as is_valid_url


LOGLEVEL = env.get('LOGLEVEL', 'WARN').upper()
root_logger = logging.getLogger()
handler = root_logger.handlers[0]
root_logger.setLevel(LOGLEVEL)
handler.setFormatter(logging.Formatter('[%(levelname)-8s] %(message)s'))


def shorten_url(event, context):
    data = {
        'user': event.get('user'),
        'path': event['data'].get('custom_path'),
        'links_to': event['data']['url'],
    }
    try:
        u = ShortUrl(**data)
        print(u)
        return repo.save(u).asdict()
    except ValueError as ex:
        raise Exception(str(ex))
    except repo.DuplicateKey:
        raise Exception('Path is already taken')


def list_urls(event, context):
    return {"urls": [u.asdict() for u in repo.find_by_user(event['user'])]}


def delete_url(event, context):
    data = {
        'user': event['user'],
        'path': event['path'],
    }
    try:
        repo.delete(**data)
    except repo.KeyNotFound:
        raise Exception('forbidden')


def edit_url(event, context):
    path, user, data = event.values()
    try:
        return repo.update(path=path, user=user, data=data).asdict()
    except repo.KeyNotFound:
        raise Exception('forbidden')
    except repo.DuplicateKey:
        raise Exception('Path is already taken')
