import pytest
from datetime import datetime
import unicodedata

from argon2 import PasswordHasher
from pymongo.collection import Collection
from pymongo import MongoClient
from bson.objectid import ObjectId

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
    CREATOR_ID_IDENTIFIER,
    VISITS_COUNT_IDENTIFIER,
    USER_ID_IDENTIFIER,
    USERNAME_IDENTIFIER,
    PASSWORD_HASH_IDENTIFIER,
    ACCOUNT_CREATION_DATE_IDENTIFIER,
)

@pytest.fixture()
def mongo_client():
    client = MongoClient(host="localhost", port=27017)
    client.tests.drop_collection("users")
    client.tests.drop_collection("urls")
    return client

@pytest.fixture
def mongo_client_with_data(mongo_client):
    users: Collection = mongo_client.tests.users
    urls: Collection = mongo_client.tests.urls

    ph = PasswordHasher()

    # Creator 1
    result = users.insert_one(
        {
            USERNAME_IDENTIFIER: "example_user1",
            PASSWORD_HASH_IDENTIFIER: ph.hash(unicodedata.normalize("NFKC", "S3cret_p4$$word")),
            ACCOUNT_CREATION_DATE_IDENTIFIER: datetime(2010, 6, 1, 9, 0, 0),
        }
    )
    user_id1 = result.inserted_id

    # Creator 2
    result = users.insert_one(
        {
            USERNAME_IDENTIFIER: "example_user2",
            PASSWORD_HASH_IDENTIFIER: ph.hash(unicodedata.normalize("NFKC", "2nd_S3cret_p4$$word")),
            ACCOUNT_CREATION_DATE_IDENTIFIER: datetime(2017, 6, 1, 9, 0, 0),
        }
    )
    user_id2 = result.inserted_id

    # Creator 3
    users.insert_one(
        {
            USERNAME_IDENTIFIER: "example_user3",
            PASSWORD_HASH_IDENTIFIER: ph.hash(unicodedata.normalize("NFKC", "eXtRa_S3cret_p4$$word")),
            ACCOUNT_CREATION_DATE_IDENTIFIER: datetime(2019, 6, 1, 9, 0, 0),
        }
    )
    
    # Store 1st address (user 1)
    urls.insert_one(
        {
            LONG_URL_IDENTIFIER: "https://www.example.com/long/relative/path/?var=5#fragment",
            SHORT_ID_IDENTIFIER: "abcdef1",
            URL_CREATION_DATE_IDENTIFIER: datetime(2020, 6, 1, 9, 0, 0),
            CREATOR_ID_IDENTIFIER: user_id1,
            VISITS_COUNT_IDENTIFIER: 125,
        }
    )

    # Store 2nd address (user 1)
    urls.insert_one(
        {
            LONG_URL_IDENTIFIER: "https://www.example2.com/path",
            SHORT_ID_IDENTIFIER: "shortid",
            URL_CREATION_DATE_IDENTIFIER: datetime(2020, 1, 1, 9, 0, 0),
            CREATOR_ID_IDENTIFIER: user_id1,
            VISITS_COUNT_IDENTIFIER: 0,
        }
    )

    # Store 3nd address (user 2)
    urls.insert_one(
        {
            LONG_URL_IDENTIFIER: "https://www.website.com/path",
            SHORT_ID_IDENTIFIER: "1234567",
            URL_CREATION_DATE_IDENTIFIER: datetime(2020, 10, 1, 9, 0, 0),
            CREATOR_ID_IDENTIFIER: user_id2,
            VISITS_COUNT_IDENTIFIER: 9,
        }
    )

    return mongo_client

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
        user_id = auth.register_user(creator_username, "S3cret_p4$$word")  # ensure user exists

        am.store_url_and_id(long_url, short_id, user_id)
        result = urls.find_one({LONG_URL_IDENTIFIER: long_url})

        assert result is not None
        assert result[SHORT_ID_IDENTIFIER] == short_id
        assert result[CREATOR_ID_IDENTIFIER] == user_id
        assert URL_CREATION_DATE_IDENTIFIER in result

    def test_store_url_and_id_raises_if_url_invalid(self, mongo_client):
        am = AddressManager(mongo_client.tests)

        long_url = "ht://wwwww.example.c5/"
        short_id = "abcdef1"
        creator_username = "example_user1"

        auth = UserAuthenticator(mongo_client.tests)
        user_id = auth.register_user(creator_username, "S3cret_p4$$word")  # ensure user exists

        with pytest.raises(UrlInvalidError):
            am.store_url_and_id(long_url, short_id, user_id)

    def test_store_url_and_id_raises_if_creator_nonexistent(self, mongo_client):
        am = AddressManager(mongo_client.tests)

        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_id = ObjectId(b"example_user")  # user does not exist in users collection

        with pytest.raises(UserNotFoundError):
            am.store_url_and_id(long_url, short_id, creator_id)

    def test_store_url_and_id_raises_if_url_exists(self, mongo_client_with_data):
        users: Collection = mongo_client_with_data.tests.users
        am = AddressManager(mongo_client_with_data.tests)

        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        short_id = "abcdef1"
        creator_username = "example_user3"
        user_id = users.find_one({USERNAME_IDENTIFIER: creator_username})[USER_ID_IDENTIFIER]

        with pytest.raises(UrlExistsError):
            am.store_url_and_id(long_url, short_id, user_id)

    def test_lookup_short_id(self, mongo_client_with_data):
        am = AddressManager(mongo_client_with_data.tests)
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        
        assert am.lookup_short_id("abcdef1") == long_url
        with pytest.raises(UrlNotFoundError):
            am.lookup_short_id("xyz1234")

    def test_lookup_short_id_count_visit(self, mongo_client_with_data):
        urls: Collection = mongo_client_with_data.tests.urls
        am = AddressManager(mongo_client_with_data.tests)
        short_id = "abcdef1"
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        visits = urls.find_one({SHORT_ID_IDENTIFIER: short_id})[VISITS_COUNT_IDENTIFIER]
        assert am.lookup_short_id(short_id, count_visit=True) == long_url
        assert urls.find_one({SHORT_ID_IDENTIFIER: short_id})[VISITS_COUNT_IDENTIFIER] == visits + 1

    def test_delete_url(self, mongo_client_with_data):
        urls: Collection = mongo_client_with_data.tests.urls
        am = AddressManager(mongo_client_with_data.tests)
        long_url = "https://www.example.com/long/relative/path/?var=5#fragment"
        
        assert urls.find_one({LONG_URL_IDENTIFIER: long_url}) is not None
        with pytest.raises(UrlNotFoundError):
            am.delete_url("https://www.example1.com")
        am.delete_url(long_url)
        assert urls.find_one({LONG_URL_IDENTIFIER: long_url}) is None

    def test_delete_short_id(self, mongo_client_with_data):
        urls: Collection = mongo_client_with_data.tests.urls
        am = AddressManager(mongo_client_with_data.tests)
        short_id = "abcdef1"
        
        assert urls.find_one({SHORT_ID_IDENTIFIER: short_id}) is not None
        with pytest.raises(UrlNotFoundError):
            am.delete_short_id("1111111")
        am.delete_short_id(short_id)
        assert urls.find_one({SHORT_ID_IDENTIFIER: short_id}) is None

    def test_compose_shortened_url(self):
        # Trailing slash
        assert AddressManager.compose_shortened_url(
            "https://www.example.com/", 
            "shortid"
        ) == "https://www.example.com/shortid"

        # No trailing slash
        assert AddressManager.compose_shortened_url(
            "https://www.example.com",
            "shortid"
        ) == "https://www.example.com/shortid"

    def test_lookup_user_urls(self, mongo_client_with_data):
        am = AddressManager(mongo_client_with_data.tests)
        user_id1 = am._users.find_one({USERNAME_IDENTIFIER: "example_user1"})[USER_ID_IDENTIFIER]
        user_id3 = am._users.find_one({USERNAME_IDENTIFIER: "example_user3"})[USER_ID_IDENTIFIER]
        assert len(am.lookup_user_urls(user_id1)) == 2
        assert len(am.lookup_user_urls(user_id3)) == 0
        assert LONG_URL_IDENTIFIER in am.lookup_user_urls(user_id1)[0]
        assert SHORT_ID_IDENTIFIER in am.lookup_user_urls(user_id1)[0]
        with pytest.raises(UserNotFoundError):
            am.lookup_user_urls(ObjectId(b"_nonexistent"))
