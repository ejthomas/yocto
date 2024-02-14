import pytest
from datetime import datetime

from pymongo.collection import Collection
from pytest_mongo import factories

from yocto.address import AddressManager
from yocto.auth import UserAuthenticator
from yocto.lib.exceptions import (
    UrlNotFoundError,
    UrlInvalidError,
    UrlExistsError,
    UserNotFoundError
)
from yocto.lib.utils import (
    LONG_URL_IDENTIFIER,
    SHORT_ID_IDENTIFIER,
    URL_CREATION_DATE_IDENTIFIER,
    CREATOR_USERNAME_IDENTIFIER,
)

mongo_noproc = factories.mongo_noproc(host="localhost", port=27017)
mongo_client = factories.mongodb("mongo_noproc")

class TestAddressManager:
    def test_extract_id_from_short_url(self):
        assert AddressManager.extract_id_from_short_url("https://yoc.to/1234567") == "1234567"
        with pytest.raises(UrlInvalidError):
            AddressManager.extract_id_from_short_url("httpz://yoc.to/1234567")
        with pytest.raises(UrlInvalidError):
            AddressManager.extract_id_from_short_url("https://yoc.to.x.y.z/1234567")
        with pytest.raises(UrlInvalidError):
            AddressManager.extract_id_from_short_url("https://yoc.to 1234567")

    def test_generate_short_id(self, mongo_client):
        am = AddressManager(mongo_client.tests)
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        for length in range(4, 12):
            short_id = am.generate_short_id(length=length)
            assert all([c in alphabet for c in short_id])
            assert len(short_id) == length

    def test_store_url_and_id(self, mongo_client):
        urls: Collection = mongo_client.tests.urls
        am = AddressManager(mongo_client.tests)

        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"

        auth = UserAuthenticator(mongo_client.tests)
        auth.register_user(creator_username, "S3cret_p4$$word")  # ensure user exists

        am.store_url_and_id(long_url, short_id, creator_username)
        result = urls.find_one({LONG_URL_IDENTIFIER: long_url})

        assert result is not None
        assert result[SHORT_ID_IDENTIFIER] == short_id
        assert result[CREATOR_USERNAME_IDENTIFIER] == creator_username
        assert URL_CREATION_DATE_IDENTIFIER in result

    def test_store_url_and_id_raises_if_url_invalid(self, mongo_client):
        am = AddressManager(mongo_client.tests)

        long_url = "ht://wwwww.example.c5/"
        short_id = "abcdef1"
        creator_username = "example_user1"

        auth = UserAuthenticator(mongo_client.tests)
        auth.register_user(creator_username, "S3cret_p4$$word")  # ensure user exists

        with pytest.raises(UrlInvalidError):
            am.store_url_and_id(long_url, short_id, creator_username)

    def test_store_url_and_id_raises_if_creator_nonexistent(self, mongo_client):
        am = AddressManager(mongo_client.tests)

        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"  # user does not exist in users collection

        with pytest.raises(UserNotFoundError):
            am.store_url_and_id(long_url, short_id, creator_username)

    def test_store_url_and_id_raises_if_url_exists(self, mongo_client):
        urls: Collection = mongo_client.tests.urls
        am = AddressManager(mongo_client.tests)

        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"

        urls.insert_one(
            {
                LONG_URL_IDENTIFIER: long_url,
                SHORT_ID_IDENTIFIER: short_id,
                URL_CREATION_DATE_IDENTIFIER: datetime.now(),
                CREATOR_USERNAME_IDENTIFIER: creator_username,
            }
        )

        auth = UserAuthenticator(mongo_client.tests)
        auth.register_user(creator_username, "S3cret_p4$$word")  # ensure user exists

        with pytest.raises(UrlExistsError):
            am.store_url_and_id(long_url, short_id, creator_username)

    def test_lookup_short_id(self, mongo_client):
        urls: Collection = mongo_client.tests.urls
        am = AddressManager(mongo_client.tests)
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"
        urls.insert_one(
            {
                LONG_URL_IDENTIFIER: long_url,
                SHORT_ID_IDENTIFIER: short_id,
                URL_CREATION_DATE_IDENTIFIER: datetime.now(),
                CREATOR_USERNAME_IDENTIFIER: creator_username,
            }
        )
        assert am.lookup_short_id("abcdef1") == long_url
        with pytest.raises(UrlNotFoundError):
            am.lookup_short_id("xyz1234")

    def test_delete_url(self, mongo_client):
        urls: Collection = mongo_client.tests.urls
        am = AddressManager(mongo_client.tests)
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"
        urls.insert_one(
            {
                LONG_URL_IDENTIFIER: long_url,
                SHORT_ID_IDENTIFIER: short_id,
                URL_CREATION_DATE_IDENTIFIER: datetime.now(),
                CREATOR_USERNAME_IDENTIFIER: creator_username,
            }
        )
        assert urls.find_one({LONG_URL_IDENTIFIER: long_url}) is not None
        with pytest.raises(UrlNotFoundError):
            am.delete_url("https://www.example1.com")
        am.delete_url(long_url)
        assert urls.find_one({LONG_URL_IDENTIFIER: long_url}) is None

    def test_delete_short_id(self, mongo_client):
        urls: Collection = mongo_client.tests.urls
        am = AddressManager(mongo_client.tests)
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user1"
        urls.insert_one(
            {
                LONG_URL_IDENTIFIER: long_url,
                SHORT_ID_IDENTIFIER: short_id,
                URL_CREATION_DATE_IDENTIFIER: datetime.now(),
                CREATOR_USERNAME_IDENTIFIER: creator_username,
            }
        )
        assert urls.find_one({SHORT_ID_IDENTIFIER: short_id}) is not None
        with pytest.raises(UrlNotFoundError):
            am.delete_short_id("1234567")
        am.delete_short_id(short_id)
        assert urls.find_one({SHORT_ID_IDENTIFIER: short_id}) is None
