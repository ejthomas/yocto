from datetime import datetime
import regex
import unicodedata

from pymongo.collection import Collection
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from yocto.lib.exceptions import (
    UsernameInvalidError,
    UserExistsError,
    UserNotFoundError,
    PasswordInvalidError,
    PasswordMismatchError
)
from yocto.lib.utils import (
    _verify_type,
    USERNAME_IDENTIFIER,
    PASSWORD_HASH_IDENTIFIER,
    ACCOUNT_CREATION_DATE_IDENTIFIER,
    CREATOR_USERNAME_IDENTIFIER,
)

ph = PasswordHasher()

USERNAME_MIN_LENGTH = 1
USERNAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 100

class UserAuthenticator:
    def __init__(self, database):
        """
        Class for managing user authentication and credential storage in database.

        Methods in this class allow registration of new users in the database
        and authentication of existing users with credentials. Passwords are
        securely hashed and salted using Argon2id. When a user is deleted, it is
        ensured that all links created by the user are also removed.

        :param database: Database containing the users and urls collections.
        :type database: pymongo.database.Database
        """
        self._users: Collection = database.users
        self._urls: Collection = database.urls

    @staticmethod
    def validate_username(username):
        """
        Validate the provided username.

        Username must be unique in the database and between auth.USERNAME_MIN_LENGTH 
        and auth.USERNAME_MAX_LENGTH characters long.
        
        :param str username: The username to validate.
        
        :raises TypeError: If the username is not a string.
        :raises UsernameInvalidError: If the username cannot be used.

        :return: True if username is valid, otherwise raises.
        :rtype: bool
        """
        _verify_type(username, str)
        if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
            raise UsernameInvalidError(
                f"Length must be at least {USERNAME_MIN_LENGTH} and at most "
                f"{USERNAME_MAX_LENGTH} characters"
            )
        return True

    @staticmethod
    def validate_password(password):
        """
        Validate that a password satisfies the length and complexity 
        requirements of the application.

        Password must be between auth.PASSWORD_MIN_LENGTH and auth.PASSWORD_MAX_LENGTH characters long, 
        and contain at least one uppercase letter, lowercase letter, number and special character.
        
        :param str password: The password to validate.
        
        :raises TypeError: If the password is not a string.
        :raises PasswordInvalidError: If the password does not satisfy the
        requirements.

        :return: True if password is valid, otherwise raises.
        :rtype: bool
        """
        _verify_type(password, str)
        if len(password) < PASSWORD_MIN_LENGTH:
            raise PasswordInvalidError(f"Passwords must be at least {PASSWORD_MIN_LENGTH} characters")
        if len(password) > 100:
            raise PasswordInvalidError(f"Maximum password length {PASSWORD_MAX_LENGTH} characters")
        if regex.search(r"[\p{N}]", password) is None:
            raise PasswordInvalidError("Passwords must contain at least one number")
        if regex.search(r"[\p{Lu}]", password) is None:
            raise PasswordInvalidError("Passwords must contain at least one uppercase letter")
        if regex.search(r"[\p{Ll}]", password) is None:
            raise PasswordInvalidError("Passwords must contain at least one lowercase letter")
        if regex.search(r"[^\p{L}\p{N}]", password) is None:
            raise PasswordInvalidError("Passwords must contain at least one special character")
        return True
        

    def register_user(self, username, password):
        """
        Register a new user in the users database.

        :param str username: The username of the new user.
        :param str password: The password of the new user.

        :raises UserExistsError: If the username already exists in the database.
        """
        self.validate_username(username)
        if self._users.find_one({USERNAME_IDENTIFIER: username}) is not None:
            raise UserExistsError
        self.validate_password(password)
        self._users.insert_one(
            {
                USERNAME_IDENTIFIER: username,
                PASSWORD_HASH_IDENTIFIER: ph.hash(unicodedata.normalize("NFKC", password)),
                ACCOUNT_CREATION_DATE_IDENTIFIER: datetime.now(),
            }
        )

    def authenticate_user(self, username, password):
        """
        Authenticate a user's credentials against the database.

        :param str username: The user's username.
        :param str password: The user's password.

        :raises UserNotFoundError: If the username is not in the database.
        :raises PasswordMismatchError: If the user's password is not correct.

        :return: True if password is correct, otherwise raises.
        :rtype: bool
        """
        _verify_type(username, str)
        _verify_type(password, str)
        user_record = self._users.find_one({USERNAME_IDENTIFIER: username})
        if user_record is None:
            raise UserNotFoundError
        try:
            return ph.verify(
                user_record[PASSWORD_HASH_IDENTIFIER],
                unicodedata.normalize("NFKC", password)
            )
        except VerifyMismatchError:
            raise PasswordMismatchError

    def delete_user(self, username):
        """
        Delete a user account from the database.

        :param str username: The username of the account to delete.

        :raises UserNotFoundError: If `username` is not a username in the 
            users database collection.
        """
        _verify_type(username, str)
        # Delete user's URLs
        self._urls.delete_many({CREATOR_USERNAME_IDENTIFIER: username})
        # Delete user account
        result = self._users.delete_one({USERNAME_IDENTIFIER: username})
        # Raise exception if no account deleted
        if result.deleted_count == 0:
            raise UserNotFoundError
