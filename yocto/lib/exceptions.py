class UsernameInvalidError(Exception):
    pass


class PasswordInvalidError(Exception):
    pass


class UserExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class PasswordMismatchError(Exception):
    pass


class UrlInvalidError(Exception):
    pass


class UrlNotFoundError(Exception):
    pass


class UrlExistsError(Exception):
    pass
