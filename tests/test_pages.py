import pytest

import regex
from flask import session, url_for, g

from yocto import create_app
from yocto.db import init_db, get_db
from yocto.auth import UserAuthenticator
from yocto.address import AddressManager
from yocto.lib.utils import LONG_URL_IDENTIFIER, SHORT_ID_IDENTIFIER

@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "DATABASE": "tests"})
    with app.app_context():
        init_db()  # work with a fresh database
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


def test_index_root(client):
    response = client.get("/pages/")  # root
    assert b"<title>Yocto - Home</title>" in response.data  # inherits from base
    assert b"<nav>" in response.data  # navigation bar displaying
    assert regex.search(r"<header>\s+<h2>Home</h2>\s+</header>", response.text)  # display header
    assert b"Account deleted successfully." not in response.data  # no deletion message
    assert b"Log out successful." not in response.data  # no logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text


def test_index_disp(client):
    response = client.get("/pages/index/user-logged-out", follow_redirects=True)  # logout message route
    assert b"Account deleted successfully." not in response.data  # no deletion message
    assert b"Log out successful." in response.data  # display logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text

    response = client.get("/pages/index/account-delete-success", follow_redirects=True)  # account deleted message route
    assert b"Account deleted successfully." in response.data  # show deletion message
    assert b"Log out successful." not in response.data  # no logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text


def test_signup_get(client):
    response = client.get("/pages/signup/")
    assert b'<form action = "/pages/signup" method = "post">' in response.data  # display the form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # pw value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # rep_pw value field empty


def test_signup_post_non_matching_pw(client):
    response = client.post("/pages/signup/", data={"uname": "test_user", "pw": "V4l1d_password", "rep_pw": "other_V4l1d_password"})
    assert b"Passwords do not match." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"test_user"[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"other_V4l1d_password"[^>]*>', response.text)  # rep_pw value

def test_signup_post_invalid_uname(client):
    response = client.post("/pages/signup/", data={"uname": "", "pw": "V4l1d_password", "rep_pw": "V4l1d_password"})
    assert b"Username not valid." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # rep_pw value


def test_signup_post_invalid_pw(client):
    response = client.post("/pages/signup/", data={"uname": "test_user", "pw": "invalidpassword", "rep_pw": "invalidpassword"})
    assert b"Password not valid." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"test_user"[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"invalidpassword"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"invalidpassword"[^>]*>', response.text)  # rep_pw value


def test_signup_post_valid(client):
    with client:
        response = client.post("/pages/signup/", data={"uname": "test_user", "pw": "V4l1d_password", "rep_pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "test_user"
    assert len(response.history) == 1
    assert response.request.path == "/pages/login_success/test_user/"


def test_login_get(client):
    response = client.get("/pages/login/")
    assert b'<form action = "/pages/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # pw value field empty
    assert b"The requested user was not found." not in response.data
    assert b"Password incorrect." not in response.data


def test_login_post_unknown_user(client):
    response = client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"})
    assert b'<form action = "/pages/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"new_user"[^>]*>', response.text)  # uname value field kept
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value field kept
    assert b"The requested user was not found." in response.data


def test_login_post_wrong_pw(client, app):
    with app.app_context():
        auth = UserAuthenticator(get_db())
        auth.register_user("new_user", "V4l1d_password")
    response = client.post("/pages/login/", data={"uname": "new_user", "pw": "other_V4l1d_password"})
    assert b'<form action = "/pages/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"new_user"[^>]*>', response.text)  # uname value field kept
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"other_V4l1d_password"[^>]*>', response.text)  # pw value field kept
    assert b"Password incorrect." in response.data


def test_login_post_valid_credentials(client_with_data):
    with client_with_data as client:
        response = client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
    assert len(response.history) == 1  # redirect occurred
    assert response.request.path == "/pages/login_success/new_user/"  # correct destination


def test_login_success(client):
    response = client.get("/pages/login_success/test_name", follow_redirects=True)
    assert b'Login successful. Welcome test_name.' in response.data

def test_logout(client_with_data):
    with client_with_data as client:
        # Login as created user
        response = client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
        # Log out
        response = client.get("/pages/logout/", follow_redirects=True)
        assert "user" not in session
    assert len(response.history) == 1
    assert response.request.path == "/pages/index/user-logged-out/"

def test_account(client_with_data):
    with client_with_data as client:
        # Redirects to login if user not logged in
        response = client.get("/pages/account/", follow_redirects=True)
        assert len(response.history) == 1
        assert response.request.path == "/pages/login/"
        # Login as new_user
        client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        # Follow account route
        response = client.get("/pages/account/")
        assert regex.search(r"<header>\s+<h2>Account</h2>\s+</header>", response.text)  # display header
        assert regex.search(r"<p>\s+" + session["user"] + r"\s+</p>", response.text)  # display header
        

def test_delete(client_with_data):
    with client_with_data as client:
        # Login
        client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        response = client.get("/pages/delete/")
        assert b"Delete account" in response.data


def test_delete_confirmed_logged_in(client_with_data):
    with client_with_data as client:
        # Login as new_user
        client.post("/pages/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
        response = client.get("/pages/delete/confirmed/", follow_redirects=True)
        assert "user" not in session
    assert len(response.history) == 1
    assert response.request.path == "/pages/index/account-delete-success/"
    

def test_error(app, client):
    # Need app.test_request_context to use url_for
    with app.test_request_context():
        response = client.get(url_for("pages.error", message="An example of an error."))
        assert b"An example of an error." in response.data
    

def test_create_get(client_with_data):
    with client_with_data:
        # Login as user
        client_with_data.post(
            "/pages/login/", 
            data={"uname": "new_user", "pw": "V4l1d_password"}, 
            follow_redirects=True
        )
        response = client_with_data.get("/pages/create/")
        assert b'<form action="/pages/create/" method="post">' in response.data


def test_create_post(client_with_data):
    with client_with_data as client:
        # Login as user
        client.post(
            "/pages/login/", 
            data={"uname": "new_user", "pw": "V4l1d_password"}, 
            follow_redirects=True
        )

        # Invalid address
        response = client.post("/pages/create/", data={"url": "https://www.example.123"})
        assert b"Input is not a valid web address." in response.data

        # Address already exists
        response = client.post("/pages/create/", data={"url": "https://www.example.com"})
        assert b"abcdef1" in response.data

        # Valid new address
        response = client.post("/pages/create/", data={"url": "https://www.xyz.com"})
        db = get_db()
        result = db.urls.find_one({LONG_URL_IDENTIFIER: "https://www.xyz.com"})
        assert result is not None
        assert result[SHORT_ID_IDENTIFIER] in response.text


def test_my_links(client_with_data):
    with client_with_data as client:
        # Login as user
        client.post(
            "/pages/login/", 
            data={"uname": "new_user", "pw": "V4l1d_password"}, 
            follow_redirects=True
        )
        response = client.get("/pages/my-links/")
        assert b"https://www.example.com" in response.data
        assert b"https://www.example2.com" in response.data
        assert b"abcdef1" in response.data
        assert b"1234567" in response.data
