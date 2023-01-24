import re
import string
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import chain
from random import choice
from typing import Union

import src.link.repo as repo
from src.common.errors import ValidationError
from src.common.validations import Validations
from src.link.validators import url as is_valid_url

BACKHALF_MIN_LEN = 1
BACKHALF_MAX_LEN = 20
BACKHALF_FORMAT = '^[A-Za-z0-9_-]*$'


@dataclass
class Link(Validations):
    def validate_backhalf(self, value: str) -> str:
        return new_random_backhalf(len=7) if value is None else validate_backhalf(value)

    def validate_origin(self, value):
        if value is None:
            raise ValidationError('origin is missing')
        if not is_valid_url(value):
            raise ValidationError('origin URL is invalid')

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})

    origin: str
    user: str
    backhalf: Union[str, None] = None
    created_at: str = str(datetime.now())
    updated_at: Union[str, None] = None
    id: Union[int, None] = None


@dataclass
class LinkUpdate(Validations):
    def validate_backhalf(self, value: str):
        if value is None:
            return
        validate_backhalf(value)

    def validate_origin(self, value):
        if value is None:
            return
        if not is_valid_url(value):
            raise ValidationError('origin URL is invalid')

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})

    origin: Union[str, None] = None
    backhalf: Union[str, None] = None
    updated_at: str = str(datetime.now())


def validate_backhalf(value: str):
    if not BACKHALF_MIN_LEN <= len(value) <= BACKHALF_MAX_LEN:
        raise ValidationError(f'backhalf length invalid (valid range is {BACKHALF_MIN_LEN}-{BACKHALF_MAX_LEN})')
    if not re.match(BACKHALF_FORMAT, value):
        raise ValidationError(f'backhalf does not match regex {BACKHALF_FORMAT}')
    return value


def new_random_backhalf(len):
    while True:
        new_backhalf = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
        if not repo.is_taken(new_backhalf):
            return new_backhalf
