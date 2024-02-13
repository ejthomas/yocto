import getpass

from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("localhost", 27017, username="ejthomas", password=getpass.getpass())
db = client.yocto
users = db.users
urls = db.urls
test = db.test

@app.route("/")
def index():
    return render_template("index.html")