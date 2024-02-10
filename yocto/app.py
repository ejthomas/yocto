import getpass

from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("localhost", 27017, username="ejthomas", password=getpass.getpass())
db = client.yocto
users = db.users
urls = db.urls
test = db.test

def insert_url(creator, creation_date, full_url, short_url):
    urls.insert_one(
        {
            "creator": creator,
            "creation_date": creation_date,
            "full_url": full_url,
            "short_url": short_url,
        }
    )

def insert_user(username, password_hash, creation_date):
    users.insert_one(
        {
            "username": username,
            "password_hash": password_hash,
            "creation_date": creation_date,
        }
    )

## Example insertion of URL
# from datetime import datetime
# insert_url(
#     "ejthomas",
#     datetime.now(),
#     "https://github.com/ejthomas/yocto",
#     "https://yoc.to/abcdef01",
# )]
    
## Example insertion of user
# insert_user(
#     "ejthomas",
#     hash(example_password),  # update with more suitable password hashing process
#     datetime.now(),
# )

@app.route("/")
def index():
    return render_template("index.html")