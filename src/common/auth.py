import src.user.repo as user_repo
from src.common.errors import AuthorizationError


def user_must_be_admin(event):
    user = auth_user(event)
    if not user_repo.find_by_email(user).is_admin:
        raise AuthorizationError('you must be admin')


def user_must_be_activated(event):
    user = auth_user(event)
    if not user_repo.find_by_email(user).is_activated:
        raise AuthorizationError('user account not activated')


def auth_user(event):
    return event['auth']['user']
