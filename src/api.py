import logging
import src.repo as repo

from os import environ as env
from src.link import Link


LOGLEVEL = env.get('LOGLEVEL', 'WARN').upper()
root_logger = logging.getLogger()
handler = root_logger.handlers[0]
root_logger.setLevel(LOGLEVEL)
handler.setFormatter(logging.Formatter('[%(levelname)-8s] %(message)s'))


def create_link(event, context):
    data = {
        'origin': event['data']['origin'],
        'backhalf': event['data'].get('backhalf'),
        'user': event.get('user')
    }
    try:
        u = Link(**data)
        return repo.save(u).asdict()
    except repo.DuplicateKey:
        raise Exception('Backhalf is already taken')


def list_links(event, context):
    return {"data": [u.asdict() for u in repo.find_by_user(event['user'])]}


def delete_link(event, context):
    data = {
        'user': event['user'],
        'backhalf': event['backhalf'],
    }
    try:
        repo.delete(**data)
    except repo.KeyNotFound:
        raise Exception('forbidden')


def edit_link(event, context):
    backhalf, user, data = event.values()
    try:
        return repo.update(backhalf=backhalf, user=user, data=data).asdict()
    except repo.KeyNotFound:
        raise Exception('forbidden')
    except repo.DuplicateKey:
        raise Exception('Backhalf is already taken')
