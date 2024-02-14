from datetime import datetime
from urllib.parse import urlsplit
import secrets
import math

from pymongo.collection import Collection
from validators import url

from yocto.lib.utils import _verify_type
from yocto.lib.exceptions import (
    UrlInvalidError,
    UrlExistsError,
    UrlNotFoundError,
    UserNotFoundError
)
from yocto.lib.utils import (
    LONG_URL_IDENTIFIER,
    SHORT_ID_IDENTIFIER,
    CREATION_DATE_IDENTIFIER,
    CREATOR_USERNAME_IDENTIFIER,
    USERNAME_IDENTIFIER,
)

class AddressManager:
    def __init__(self, urls_collection, users_collection):
        """
        Class to manage URLs and their corresponding shortened versions.

        Provides methods to store and manipulate database entries matching
        long URLs (the targets for shortening) and the corresponding shortened 
        URLs which will redirect to them. A shortened URL takes the form
        "https://<shortener_domain>/<ID>", where the ID is a short alphanumeric
        string unique to the original URL the short address redirects to. It
        is the ID which will be stored in the database, as the rest of the URL
        can be constructed outside the database.

        :param urls_collection: The collection where web addresses are stored.
        :type urls_collection: pymongo.collection.Collection
        :param users_collection: The collection where user credentials are stored.
        :type users_collection: pymongo.collection.Collection
        """
        self._urls: Collection = urls_collection
        self._users: Collection = users_collection

    @staticmethod
    def extract_id_from_short_url(short_url):
        """
        Extract the ID part of the shortened URL.

        In the shortened URL, only the ID (e.g. the "123" part, after the "/", 
        in "example.com/123") changes between different addresses. Therefore 
        for storage in the database, the ID part should be extracted and 
        only this part stored. The full shortened address can be constructed 
        by combining this with the domain name.

        :param str short_url: The short URL from which the ID will be 
            extracted.

        :raises UrlInvalidError: If `short_url` is not a valid URL.

        :return: The ID part of the URL.
        :rtype: str

        *Examples*
        >>> extract_id_from_short_url("https://yoc.to/1234567")
        "1234567"
        """
        if not url(short_url):
            raise UrlInvalidError
        split_url = urlsplit(short_url)
        return split_url.path.removeprefix("/")
        
    def generate_short_id(
            self,
            length=7,
        ):
        """
        Generate a random short ID.
        
        To ensure the output is unpredictable, the system's source of 
        cryptographic randomness is used. Short IDs generated are `length`
        characters long, comprising numbers, uppercase and lowercase
        letters, "-" and "_" (a 64-character encoding). The returned value 
        is ensured to be unique in the database.

        :param int length: The number of characters in the returned ID 
            (default 7).

        :return: The generated short ID.
        :rtype: str
        """
        while True:
            if 6 * length % 8 == 0:
                short_id = secrets.token_urlsafe(6 * length // 8)
            else:
                # Complexity of string is non-integer number of bytes
                # To ensure all `length`-bit strings possible, round up
                # bytes then truncate result
                short_id = secrets.token_urlsafe(math.ceil(6 * length / 8))[:length]
            if self._urls.find_one({SHORT_ID_IDENTIFIER: short_id}) is None:
                break
        return short_id

    def store_url_and_id(self, long_url, short_id, creator_username):
        """
        Store a long URL with its associated shortened ID in the collection.

        :param str long_url: The long URL to which the shortened address points.
        :param str short_id: The ID part of the shortened URL.
        :param str creator_username: The username of the account creating the 
            database entry.
        
        :raises UrlInvalidError: If `long_url` is not a valid URL.
        :raises UserNotFoundError: If `creator_username` is not registered in
            the users collection of the database.
        :raises UrlExistsError: If `long_url` is already in the urls collection.
        """
        if not url(long_url):
            raise UrlInvalidError
        for var in [long_url, short_id, creator_username]:
            _verify_type(var, str)
        if self._users.find_one({USERNAME_IDENTIFIER: creator_username}) is None:
            raise UserNotFoundError
        if self._urls.find_one({LONG_URL_IDENTIFIER: long_url}) is not None:
            raise UrlExistsError
        self._urls.insert_one(
            {
                LONG_URL_IDENTIFIER: long_url,
                SHORT_ID_IDENTIFIER: short_id,
                CREATION_DATE_IDENTIFIER: datetime.now(),
                CREATOR_USERNAME_IDENTIFIER: creator_username,
            }
        )
        

    def lookup_short_id(self, short_id):
        """
        Retrieve the long URL corresponding to the provided short ID.

        :param str short_id: The shortened URL to look up in the database.

        :raises UrlNotFoundError: If the URL to look up is not in the database.

        :return: The long URL to which the shortened URL should redirect.
        :rtype: str
        """
        _verify_type(short_id, str)
        result = self._urls.find_one({SHORT_ID_IDENTIFIER: short_id})
        if result is None:
            raise UrlNotFoundError
        return result[LONG_URL_IDENTIFIER]

    def delete_url(self, long_url):
        """
        Delete an entry from the database based on its long URL.

        :param str long_url: The long URL to remove.

        :raises UrlNotFoundError: If the long URL specified is not present
            in the database.
        """
        _verify_type(long_url, str)
        result = self._urls.delete_one({LONG_URL_IDENTIFIER: long_url})
        if result.deleted_count == 0:
            raise UrlNotFoundError

    def delete_short_id(self, short_id):
        """
        Delete an entry from the database based on its short ID.

        :param str short_id: The short ID to remove.

        :raises UrlNotFoundError: If the short ID specified is not present
            in the database.
        """
        _verify_type(short_id, str)
        result = self._urls.delete_one({SHORT_ID_IDENTIFIER: short_id})
        if result.deleted_count == 0:
            raise UrlNotFoundError
