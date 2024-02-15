# from flask import Flask, render_template
# from pymongo import MongoClient

# from auth import UserAuthenticator

# app = Flask(__name__)

# client = MongoClient("localhost", 27017)
# db = client.yocto
# users = db.users
# urls = db.urls

# auth = UserAuthenticator(users)

# @app.route("/")
# @app.route("/index/")
# def index():
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run("localhost", port=8000, debug=True)