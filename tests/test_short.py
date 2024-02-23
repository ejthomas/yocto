import pytest

from flask import session, url_for, g, current_app

from yocto import create_app
from yocto.db import init_db, get_db
from yocto.auth import UserAuthenticator
from yocto.address import AddressManager
from yocto.lib.utils import LONG_URL_IDENTIFIER, SHORT_ID_IDENTIFIER


@pytest.fixture()
def app():
    app = create_app(test_config={"TESTING": True, "DATABASE": "tests"})
    with app.app_context():
        init_db()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def client_with_data(app):
    # Create new user
    with app.app_context():
        db = get_db()
        auth = UserAuthenticator(db)
        auth.register_user("new_user", "V4l1d_password")
        am = AddressManager(db)
        am.store_url_and_id("https://www.example.com", "abcdef1", "new_user")
        am.store_url_and_id("https://www.example2.com", "1234567", "new_user")
    return app.test_client()


def test_index_root(client, app):
    response = client.get("/", follow_redirects=True)
    assert len(response.history) == 1
    with app.test_request_context():
        assert response.request.path == url_for("pages.index")


def test_index_redirect_valid(client_with_data):
    response = client_with_data.get("/abcdef1")
    assert response.status_code == 302
    assert response.location == "https://www.example.com"

    # Accepts trailing slash
    response = client_with_data.get("/abcdef1/")
    assert response.status_code == 302
    assert response.location == "https://www.example.com"


def test_index_redirect_invalid(client_with_data, app):
    response = client_with_data.get("/notreal", follow_redirects=True)
    assert len(response.history) == 1
    with app.test_request_context():
        assert url_for("pages.error") in response.request.path
    assert b"shortened address is not valid" in response.data