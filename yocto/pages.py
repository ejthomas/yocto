from flask import Blueprint, render_template, request, redirect, url_for
from pymongo import MongoClient

from yocto.auth import UserAuthenticator

bp = Blueprint("pages", __name__)

@bp.route("/")
@bp.route("/index/")
def index():
    return render_template("pages/index.html")

@bp.route("/signup/", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        user = request.form["uname"]
        if request.form["pw"] == request.form["rep_pw"]:
            return redirect(url_for("pages.login_success", user=user))
        else:
            return render_template(
                "pages/signup.html", 
                message="Passwords do not match.",
                form=request.form,
            )
    else:
        form = {"uname": "", "pw": "", "rep_pw": ""}
        return render_template(
            "pages/signup.html", 
            message="",
            form=form,
        )

@bp.route("/login/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = request.form["uname"]
        if request.form["pw"] == "asdf":
            return redirect(url_for("pages.login_success", user=user))
        else:
            return render_template(
                "pages/login.html", 
                form=request.form,
                message="Password incorrect.",
            )
    else:
        form = {"uname": "", "pw": ""}
        return render_template(
            "pages/login.html", 
            form=form,
            message="",
        )

@bp.route("/login_success/<user>/")
def login_success(user):
    return render_template("pages/login_success.html", name=user)
