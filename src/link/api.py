from os import environ as env
from typing import Dict

import src.link.repo as link_repo
from src.common.auth import auth_user, user_must_be_activated
from src.common.errors import ApplicationError, AuthorizationError
from src.link.link import Link, LinkUpdate

DOMAIN_NAME = env['BUCKET_NAME']


def get_info(event, context):
    return {
        'base_url': get_base_url()
    }


def create_link(event, context):
    user_must_be_activated(event)
    try:
        new_link = Link(
            **event['data'],
            user=auth_user(event),
        )
        return as_lambda_response(link_repo.create(new_link))
    except link_repo.LinkAlreadyExistsError:
        raise ApplicationError('backhalf is already taken')


def list_links(event, context):
    user_must_be_activated(event)
    user = auth_user(event)
    return {
        'data': [as_lambda_response(link) for link in link_repo.find_by_user(user)]
    }


def update_link(event, context):
    user_must_be_activated(event)
    try:
        updated_link = link_repo.update_if_owned_by_user(
            backhalf=event['backhalf'],
            link_update=LinkUpdate(**event['data']),
            user=auth_user(event),
        )
        return as_lambda_response(updated_link)
    except (link_repo.LinkNotFoundError, link_repo.NotOwnedByUserError):
        raise AuthorizationError('you are not allowed to update this link')
    except link_repo.LinkAlreadyExistsError:
        raise ApplicationError('backhalf is already taken')


def delete_link(event, context):
    user_must_be_activated(event)
    try:
        link_repo.delete_if_owned_by_user(
            backhalf=event['backhalf'],
            user=auth_user(event),
        )
    except (link_repo.LinkNotFoundError, link_repo.NotOwnedByUserError):
        raise AuthorizationError('you are not allowed to delete this link')


def get_base_url():
    return f'https://{DOMAIN_NAME}/'


def as_lambda_response(link: Link) -> Dict:
    raw_data = link.asdict()
    raw_data.pop('id', None)
    return {
        **raw_data,
        'url': f'{get_base_url()}{link.backhalf}',
    }
