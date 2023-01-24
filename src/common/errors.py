class FunctionalError(Exception):
    def __init__(self, message):
        super().__init__(f'{self.__class__.__name__}: {message}')


class ApplicationError(FunctionalError):
    pass


class ValidationError(FunctionalError):
    pass


class NotFoundError(FunctionalError):
    pass


class AuthorizationError(FunctionalError):
    pass
