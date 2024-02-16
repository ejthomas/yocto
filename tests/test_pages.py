import pytest

import regex
from flask import session, url_for

from yocto import create_app
from yocto.db import init_db, get_db
from yocto.auth import UserAuthenticator

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.app_context():
        init_db()  # work with a fresh database
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def client_with_new_user(app):
    # Create new user
    with app.app_context():
        auth = UserAuthenticator(get_db())
        auth.register_user("new_user", "V4l1d_password")
    return app.test_client()


def test_index_root(client):
    response = client.get("/")  # root
    assert b"<title>Yocto - Home</title>" in response.data  # inherits from base
    assert b"<nav>" in response.data  # navigation bar displaying
    assert regex.search(r"<header>\s+<h2>Home</h2>\s+</header>", response.text)  # display header
    assert b"Account deleted successfully." not in response.data  # no deletion message
    assert b"Log out successful." not in response.data  # no logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text

def test_index_alt_route(client):
    response = client.get("/index/")  # index route
    assert response.data == client.get("/").data

def test_index_disp(client):
    response = client.get("/index/user-logged-out", follow_redirects=True)  # logout message route
    assert b"Account deleted successfully." not in response.data  # no deletion message
    assert b"Log out successful." in response.data  # display logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text

    response = client.get("/index/account-delete-success", follow_redirects=True)  # account deleted message route
    assert b"Account deleted successfully." in response.data  # show deletion message
    assert b"Log out successful." not in response.data  # no logout message
    assert b"Welcome to Yocto URL shortener." in response.data  # welcome text


def test_signup_get(client):
    response = client.get("/signup/")
    assert b'<form action = "/signup" method = "post">' in response.data  # display the form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # pw value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # rep_pw value field empty


def test_signup_post_non_matching_pw(client):
    response = client.post("/signup/", data={"uname": "test_user", "pw": "V4l1d_password", "rep_pw": "other_V4l1d_password"})
    assert b"Passwords do not match." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"test_user"[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"other_V4l1d_password"[^>]*>', response.text)  # rep_pw value

def test_signup_post_invalid_uname(client):
    response = client.post("/signup/", data={"uname": "", "pw": "V4l1d_password", "rep_pw": "V4l1d_password"})
    assert b"Username not valid." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # rep_pw value


def test_signup_post_invalid_pw(client):
    response = client.post("/signup/", data={"uname": "test_user", "pw": "invalidpassword", "rep_pw": "invalidpassword"})
    assert b"Password not valid." in response.data
    # Keep form fill values
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"test_user"[^>]*>', response.text)  # uname value
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"invalidpassword"[^>]*>', response.text)  # pw value
    assert regex.search(r'<input[^>]*name\s?\=\s?"rep_pw"[^>]*value\s?\=\s?"invalidpassword"[^>]*>', response.text)  # rep_pw value


def test_signup_post_valid(client):
    with client:
        response = client.post("/signup/", data={"uname": "test_user", "pw": "V4l1d_password", "rep_pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "test_user"
    assert len(response.history) == 1
    assert response.request.path == "/login_success/test_user/"


def test_login_get(client):
    response = client.get("/login/")
    assert b'<form action = "/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?""[^>]*>', response.text)  # uname value field empty
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?""[^>]*>', response.text)  # pw value field empty
    assert b"The requested user was not found." not in response.data
    assert b"Password incorrect." not in response.data


def test_login_post_unknown_user(client):
    response = client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"})
    assert b'<form action = "/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"new_user"[^>]*>', response.text)  # uname value field kept
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"V4l1d_password"[^>]*>', response.text)  # pw value field kept
    assert b"The requested user was not found." in response.data


def test_login_post_wrong_pw(client, app):
    with app.app_context():
        auth = UserAuthenticator(get_db())
        auth.register_user("new_user", "V4l1d_password")
    response = client.post("/login/", data={"uname": "new_user", "pw": "other_V4l1d_password"})
    assert b'<form action = "/login/" method = "post">' in response.data # display form
    assert regex.search(r'<input[^>]*name\s?\=\s?"uname"[^>]*value\s?\=\s?"new_user"[^>]*>', response.text)  # uname value field kept
    assert regex.search(r'<input[^>]*name\s?\=\s?"pw"[^>]*value\s?\=\s?"other_V4l1d_password"[^>]*>', response.text)  # pw value field kept
    assert b"Password incorrect." in response.data


def test_login_post_valid_credentials(client_with_new_user):
    with client_with_new_user as client:
        response = client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
    assert len(response.history) == 1  # redirect occurred
    assert response.request.path == "/login_success/new_user/"  # correct destination


def test_login_success(client):
    response = client.get("/login_success/test_name", follow_redirects=True)
    assert b'Login successful. Welcome test_name.' in response.data

def test_logout(client_with_new_user):
    with client_with_new_user as client:
        # Login as created user
        response = client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
        # Log out
        response = client.get("/logout/", follow_redirects=True)
        assert "user" not in session
    assert len(response.history) == 1
    assert response.request.path == "/index/user-logged-out/"

def test_account(client_with_new_user):
    with client_with_new_user as client:
        # Login as new_user
        client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        # Follow account route
        response = client.get("/account/")
        assert regex.search(r"<header>\s+<h2>Account</h2>\s+</header>", response.text)  # display header
        assert regex.search(r"<p>\s+" + session["user"] + r"\s+</p>", response.text)  # display header
        

def test_delete(client):
    response = client.get("/delete/")
    assert b"Delete account" in response.data


def test_delete_confirmed_logged_in(client_with_new_user):
    with client_with_new_user as client:
        # Login as new_user
        client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        assert session["user"] == "new_user"
        response = client.get("/delete/confirmed/", follow_redirects=True)
        assert "user" not in session
    assert len(response.history) == 1
    assert response.request.path == "/index/account-delete-success/"


def test_delete_confirmed_error(client_with_new_user, app):
    # Not logged in
    with client_with_new_user as client:
        response = client.get("/delete/confirmed/", follow_redirects=True)
        assert len(response.history) == 1
        assert response.request.path == "/error/"
        assert b"No user logged in." in response.data

    # Delete confirmed route with nonexistent user
    # This should be impossible to cause in the app
    with client_with_new_user as client:
        # Login
        client.post("/login/", data={"uname": "new_user", "pw": "V4l1d_password"}, follow_redirects=True)
        with app.app_context():
            # Delete user from DB
            auth = UserAuthenticator(get_db())
            auth.delete_user("new_user")
        assert session["user"] == "new_user"  # deleted user still logged in
        response = client.get("/delete/confirmed/", follow_redirects=True)
        assert len(response.history) == 1
        assert response.request.path == "/error/"
        assert b"The account has already been deleted." in response.data
