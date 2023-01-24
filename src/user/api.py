import src.user.repo as user_repo
from src.common.auth import user_must_be_admin
from src.common.errors import NotFoundError
from src.user.email_notifier import notify_account_activated, notify_request_to_join
from src.user.user import UnknownUser, User, UserUpdate


def validate_user_signup(event, context):
    if is_triggered_by_api(event):  # skip user validation when created directly via API (ie. test users)
        return event
    user_email = event['request']['userAttributes']['email']
    user_name = event['request']['userAttributes']['given_name']
    user = user_repo.find_by_email(user_email)
    if isinstance(user, UnknownUser):
        create_user(user_name, user_email)
        raise ValueError('USER_NOT_FOUND')
    if not user.is_activated:
        raise ValueError('WAITING_APPROVAL')
    return event


def create_user(user_name, user_email):
    try:
        new_user = User(email=user_email)
        user_repo.create(new_user)
        if not new_user.is_admin:
            notify_request_to_join(user_name, user_email)
    except user_repo.UserAlreadyExistsError:
        pass


def list_users(event, context):
    user_must_be_admin(event)
    return {
        'data': [u.asdict() for u in user_repo.find_all()]
    }


def update_user(event, context):
    user_must_be_admin(event)
    user_id = int(event['user_id'])
    try:
        updated_user = user_repo.update(user_id, UserUpdate(**event['data']))
        if updated_user.is_activated:
            notify_account_activated(updated_user.email)
        return updated_user.asdict()
    except user_repo.UserNotFoundError:
        raise NotFoundError(f'user {user_id} not found')


def delete_user(event, context):
    user_must_be_admin(event)
    user_repo.delete(int(event['user_id']))


def is_triggered_by_api(event):
    return event['triggerSource'] == 'PreSignUp_AdminCreateUser'
