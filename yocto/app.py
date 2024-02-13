import getpass

from flask import Flask, render_template
from pymongo import MongoClient

from auth import UserAuthenticator

app = Flask(__name__)

client = MongoClient("localhost", 27017, username="myUserAdmin", password=getpass.getpass())
db = client.yocto
users = db.users
urls = db.urls

auth = UserAuthenticator(users)

@app.route("/")
def index():
    return render_template("index.html")