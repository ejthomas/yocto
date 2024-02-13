import pytest

from pytest_mongo import factories
from argon2 import PasswordHasher

from yocto.auth import (
    UserAuthenticator,
    UsernameInvalidError,
    PasswordInvalidError,
    UserExistsError,
    UserNotFoundError,
    PasswordMismatchError
)

# Requires mongod running and available at localhost:27017
# E.g. via Docker container
mongo_noproc = factories.mongo_noproc(host="localhost", port=27017)
mongo_client = factories.mongodb("mongo_noproc")

class TestUserAuthenticator:
    def test_validate_username(self):
        assert UserAuthenticator.validate_username("username")
        assert UserAuthenticator.validate_username("Us3r_n4me")
        assert UserAuthenticator.validate_username("😊")  # unicode accepted
        assert UserAuthenticator.validate_username("\xf1")  # extended ASCII accepted
        with pytest.raises(TypeError):
            UserAuthenticator.validate_username({"$gt": ""})
        with pytest.raises(UsernameInvalidError):
            UserAuthenticator.validate_username("")  # cannot be empty
        with pytest.raises(UsernameInvalidError):
            UserAuthenticator.validate_username(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed"
                " do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            )  # too long

    def test_validate_password(self):
        assert UserAuthenticator.validate_password("Saloon1-Eternal6-Dazzler2-Regalia8")
        assert UserAuthenticator.validate_password("tVRkDmm6YHKdmEhWpu!*")
        assert UserAuthenticator.validate_password("nzTp>Pd7t\xf1AJ%wN;H^Z3")  # extended ASCII accepted
        assert UserAuthenticator.validate_password("😊tVRkDmm6YHKdmEhWpu!*")  # unicode accepted
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password("hi")  # too short
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed"
                " do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            )  # too long
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password("password1^")  # no uppercase
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password("PASSWORD1^")  # no lowercase
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password("Password!")  # no number
        with pytest.raises(PasswordInvalidError):
            UserAuthenticator.validate_password("Password1")  # no special characters
        with pytest.raises(PasswordInvalidError):
            # no special characters (unicode character is letter)
            UserAuthenticator.validate_password("Password1\u00f1")


    def test_register_user(self, mongo_client):
        auth = UserAuthenticator(mongo_client.tests.users)
        username = "test_user"
        password = "Test_p4s$word"
        auth.register_user(username, password)
        user_record = mongo_client.tests.users.find_one({"username": "test_user"})
        assert user_record is not None
        assert password not in user_record.values()
        ph = PasswordHasher()
        assert ph.verify(user_record["password_hash"], password)
        assert user_record["creation_date"] is not None
        with pytest.raises(UserExistsError):
            auth.register_user(username, "...")

    def test_authenticate_user(self, mongo_client):
        auth = UserAuthenticator(mongo_client.tests.users)
        username = "test_user"
        password = "Test_p4s$word"
        auth.register_user(username, password)
        assert auth.authenticate_user(username, password)
        with pytest.raises(PasswordMismatchError):
            auth.authenticate_user(username, "wrong_password")
        with pytest.raises(UserNotFoundError):
            auth.authenticate_user("unseen_user", "password")

    def test_register_authenticate_with_unicode(self, mongo_client):
        auth = UserAuthenticator(mongo_client.tests.users)
        username = "test_user"
        password = "Passw0rd_with_\u00f1"
        auth.register_user(username, password)
        assert auth.authenticate_user(username, "Passw0rd_with_\u006e\u0303")

    def test_delete_user(self, mongo_client):
        auth = UserAuthenticator(mongo_client.tests.users)
        username = "test_user"
        password = "Test_p4s$word"
        auth.register_user(username, password)
        assert mongo_client.tests.users.find_one({"username": "test_user"}) is not None
        auth.delete_user(username)
        assert mongo_client.tests.users.find_one({"username": "test_user"}) is None

    def test_delete_user_fails_on_injection_attempt(self, mongo_client):
        auth = UserAuthenticator(mongo_client.tests.users)
        username = "test_user"
        password = "Test_p4s$word"
        auth.register_user(username, password)
        assert mongo_client.tests.users.find_one({"username": "test_user"}) is not None
        with pytest.raises(UserNotFoundError):
            # Code parsed as string e.g. user has this username
            auth.delete_user("{'$gt': ''}")
        with pytest.raises(TypeError):
            auth.delete_user({"$gt": ""})
