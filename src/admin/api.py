from os import environ as env

import src.link.repo as link_repo
from src.common.auth import user_must_be_admin
from src.common.errors import ApplicationError, NotFoundError
from src.link.api import as_lambda_response
from src.link.link import LinkUpdate

DOMAIN_NAME = env['BUCKET_NAME']


def list_all_links(event, context):
    user_must_be_admin(event)
    return {
        'data': [as_lambda_response(link) for link in link_repo.find_all()]
    }


def update_link(event, context):
    user_must_be_admin(event)
    try:
        updated_link = link_repo.update(
            backhalf=event['backhalf'],
            link_update=LinkUpdate(**event['data']),
        )
        return as_lambda_response(updated_link)
    except link_repo.LinkNotFoundError:
        raise NotFoundError('link not found')
    except link_repo.LinkAlreadyExistsError:
        raise ApplicationError('backhalf is already taken')


def delete_link(event, context):
    user_must_be_admin(event)
    try:
        link_repo.delete(
            backhalf=event['backhalf'],
        )
    except link_repo.LinkNotFoundError:
        raise NotFoundError('link not found')


def delete_all_links(event, context):
    user_must_be_admin(event)
    link_repo.delete_all()
