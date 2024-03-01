import pytest
import os

from yocto import create_app

@pytest.fixture()
def dev_app():
    app = create_app("DevelopmentConfig")
    yield app


@pytest.fixture()
def test_app():
    app = create_app("TestingConfig")
    yield app


@pytest.fixture()
def prod_app():
    app = create_app("ProductionConfig")
    yield app


def test_development_config(dev_app):
    assert dev_app.config["DEBUG"]
    assert dev_app.config["DATABASE"] == "dev"
    assert dev_app.config["SECRET_KEY"] == "dev"


def test_testing_config(test_app):
    assert test_app.config["DEBUG"]
    assert test_app.config["TESTING"]
    assert test_app.config["DATABASE"] == "tests"
    assert test_app.config["SECRET_KEY"] == "dev"

# Production config cannot be tested on CI server due to secret key
# def test_production_config(prod_app):
#     assert not prod_app.config["DEBUG"]
#     assert prod_app.config["DATABASE"] == "yocto"
#     assert prod_app.config["SECRET_KEY"] != "dev"
