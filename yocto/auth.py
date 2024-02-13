from datetime import datetime
# import regex
import regex
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

USERNAME_IDENTIFIER = "username"
PASSWORD_HASH_IDENTIFIER = "password_hash"
CREATION_DATE_IDENTIFIER = "creation_date"

class UserAuthenticator:
    def __init__(self, database):
        self.database = database

    @staticmethod
    def validate_username(username):
        """
        Validate the provided username, ensuring it contains only supported
        characters and rejecting any that could pose a security issue.
        
        :param str username: The username to validate.
        
        :raises UsernameInvalidError: If the username cannot be used.

        :return: True if username is valid, otherwise raises.
        :rtype: bool
        """
        if not isinstance(username, str):
            raise TypeError("Username must be type 'str'")
        if not 1 <= len(username) <= 100:
            raise UsernameInvalidError("Length must be at least 1 and at most 100 characters")
        return True

    @staticmethod
    def validate_password(password):
        """
        Validate that a password satisfies the length and complexity 
        requirements of the application.
        
        :param str password: The password to validate.
        
        :raises PasswordInvalidError: If the password does not satisfy the
        requirements.

        :return: True if password is valid, otherwise raises.
        :rtype: bool
        """
        if len(password) < 8:
            raise PasswordInvalidError("Passwords must be at least 8 characters")
        if len(password) > 100:
            raise PasswordInvalidError("Maximum password length 100 characters")
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
        self.validate_username(username)
        if self.database.find_one({USERNAME_IDENTIFIER: username}) is not None:
            raise UserExistsError
        self.validate_password(password)
        self.database.insert_one(
            {
                USERNAME_IDENTIFIER: username,
                PASSWORD_HASH_IDENTIFIER: ph.hash(unicodedata.normalize("NFKC", password)),
                CREATION_DATE_IDENTIFIER: datetime.now(),
            }
        )

    def authenticate_user(self, username, password):
        self.validate_username(username)
        user_record = self.database.find_one({USERNAME_IDENTIFIER: username})
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
        self.validate_username(username)
        result = self.database.delete_one({USERNAME_IDENTIFIER: username})
        if result.deleted_count == 0:
            raise UserNotFoundError
    
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
