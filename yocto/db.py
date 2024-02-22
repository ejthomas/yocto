from flask import g, current_app
import click
from pymongo import MongoClient

def get_db():
    """
    Obtain a reference to the database.

    Using this function to get a reference to the database ensures that only
    one client is initialized which can be cleaned up after a request is made.
    After this function is called, the database is available via the global
    reference in `g`.

    :return: The global reference to the database.
    :rtype: pymongo.database.Database
    """
    if "db" not in g:
        client = MongoClient(host="localhost", port=27017)
        # if current_app.testing:
        #     g.db = client.get_database("tests")
        # else:
        #     g.db = client.get_database("yocto")
        g.db = client.get_database(current_app.config['DATABASE'])
    print(g.db.name)
    return g.db

def init_db():
    """
    Initialize the database for use with the application.

    The collections "users" and "urls" will be dropped if they exist,
    providing a blank database into which the new data can be stored.
    As the NoSQL database does not use a schema, it is not necessary to
    create the new tables as they will be generated lazily when needed.
    """
    db = get_db()
    db.drop_collection("users")
    db.drop_collection("urls")

@click.command("init-db")
def init_db_command():
    """Clear existing data in the database and initialize collections."""
    init_db()
    click.echo("Initialized the database.")

def close_db(e=None):
    """
    Clean up the database if a connection exists.

    If a database connection exists, the reference to the database in `g` will
    be removed and the client connection will be closed. If there is no 
    database connection, no action is taken.
    """
    db = g.pop("db", None)
    if db is not None:
        db.client.close()

def init_app(app):
    """
    Initialize the Flask app for database support.

    This function should be called by the application factory to register
    the database cleanup function to run after a request and to make the
    `init-db` command available to run with `flask --app yocto init-db`.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
