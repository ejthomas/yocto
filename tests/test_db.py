import pytest

from flask import g
from pymongo.database import Database
from pymongo.errors import InvalidOperation

from yocto import create_app
from yocto.db import (
    get_db,
    init_db,
    close_db,
    init_app,
)

@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "DATABASE": "tests"})
    with app.app_context():
        init_db()  # work with a fresh database
    yield app

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

### The mongo_client fixture results in errors during teardown, 
### so testing on real database "tests" for now


def test_get_db(app):
    with app.app_context():
        assert "db" not in g
        db = get_db()
        assert "db" in g
        assert isinstance(db, Database)
        assert db.name == "tests"
        db2 = get_db()
        assert db2 is db  # should be same object


def test_init_db(app):
    with app.app_context():
        db = get_db()
        db.create_collection("users")
        db.create_collection("urls")
        g.db = db

        assert "users" in g.db.list_collection_names()
        assert "urls" in g.db.list_collection_names()
        init_db()  # should drop users and urls collections
        assert "users" not in g.db.list_collection_names()
        assert "urls" not in g.db.list_collection_names()


def test_init_db_command(app, runner):
    with app.app_context():
        db = get_db()
        db.create_collection("users")
        db.create_collection("urls")
        g.db = db

        assert "users" in g.db.list_collection_names()
        assert "urls" in g.db.list_collection_names()
        result = runner.invoke(args="init-db")  # should drop users and urls collections
        assert "users" not in g.db.list_collection_names()
        assert "urls" not in g.db.list_collection_names()
        
        assert "Initialized the database." in result.output


def test_close_db(app):
    with app.app_context():
        db = get_db()
        g.db = db
        close_db()
        assert "db" not in g
        # Raises InvalidOperation if connection closed
        with pytest.raises(InvalidOperation):
            db.list_collection_names()


def test_init_app(app):
    init_app(app)
    assert "init-db" in app.cli.commands
    assert close_db in app.teardown_appcontext_funcs
