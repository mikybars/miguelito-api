from dataclasses import asdict, dataclass
from os import environ as env
from typing import Union

from src.common.errors import ValidationError
from src.common.validations import Validations

ALLOWED_ROLES = ['ADMIN', 'USER']
ALLOWED_STATUSES = ['WAITING_APPROVAL', 'ACTIVE']

MAINTAINER_EMAIL = env['MAINTAINER_EMAIL']


@dataclass
class User(Validations):
    def __post_init__(self):
        if self.email == MAINTAINER_EMAIL:
            self.role = 'ADMIN'
            self.status = 'ACTIVE'

    def validate_role(self, value):
        return validate_enum('role', value, ALLOWED_ROLES)

    def validate_status(self, value):
        return validate_enum('status', value, ALLOWED_STATUSES)

    def validate_email(self, value):
        if value is None:
            raise ValidationError('email cannot be None')

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_activated(self):
        return self.status == 'ACTIVE'

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})

    email: str
    role: str = 'USER'
    status: str = 'WAITING_APPROVAL'
    id: Union[int, None] = None


class AdminUser(User):
    def __init__(self):
        super().__init__(email='admin@example.com', role='ADMIN', status='ACTIVE')


class TestUser(User):
    def __init__(self):
        super().__init__(email='test@example.com', role='ADMIN', status='ACTIVE')


class UnknownUser(User):
    def __init__(self):
        super().__init__(email='unknown@example.com')


@dataclass
class UserUpdate(Validations):
    role: Union[str, None] = None
    status: Union[str, None] = None

    def validate_role(self, value):
        return validate_enum('role', value, ALLOWED_ROLES) if value is not None else None

    def validate_status(self, value):
        return validate_enum('status', value, ALLOWED_STATUSES) if value is not None else None

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})


def validate_enum(enum_name, value, possible_values):
    if value.upper() not in possible_values:
        raise ValidationError(f'unknown {enum_name} {value} (possible values are {possible_values})')
    return value.upper()
