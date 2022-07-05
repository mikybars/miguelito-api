import re
import string
import src.repo as repo

from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import chain
from random import choice
from src.validators import url as is_valid_url


# https://stackoverflow.com/a/54489602
@dataclass
class ShortUrl:
    def getpath(self):
        return self.__dict__.get("path")

    def setpath(self, value):
        if type(value) == property or value is None:
            self.__dict__["path"] = new_random_path(len=7)
        else:
            validate_path(value)
            self.__dict__["path"] = value

    def getlink(self):
        return self.__dict__.get("links_to")

    def setlink(self, value):
        if type(value) == property or value is None:
            raise ValueError("links_to cannot be None")
        validate_url(value)
        self.__dict__["links_to"] = value

    path: str = property(getpath, setpath)
    links_to: str = property(getlink, setlink)
    created_at: str = str(datetime.now())
    updated_at: str = None
    user: str = None

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})

    del getpath, setpath, getlink, setlink


def new_random_path(len):
    while True:
        new_path = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
        if not repo.is_taken(new_path):
            return new_path


def validate_path(value):
    path_format = "^[A-Za-z0-9_-]*$"
    if not re.match(path_format, value):
        raise ValueError(f"Path does not match regex {path_format}")


def validate_url(value):
    if not is_valid_url(value):
        raise ValueError("URL is invalid")
