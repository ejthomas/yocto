from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    session
)

from yocto.auth import UserAuthenticator
from yocto.db import get_db
from yocto.lib.exceptions import (
    UsernameInvalidError,
    PasswordInvalidError,
    UserNotFoundError,
    PasswordMismatchError,
)

bp = Blueprint("pages", __name__)

@bp.route("/")
@bp.route("/index/")
@bp.route("/index/<disp>/")
def index(disp=None):
    return render_template("pages/index.html", disp=disp)

@bp.route("/signup/", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        user = request.form["uname"]
        password = request.form["pw"]
        if request.form["pw"] == request.form["rep_pw"]:
            auth = UserAuthenticator(get_db())
            try:
                auth.register_user(user, password)
            except UsernameInvalidError:
                return render_template(
                    "pages/signup.html", 
                    message="Username not valid.",  # TODO: better message
                    form=request.form,
                )
            except PasswordInvalidError:
                return render_template(
                    "pages/signup.html", 
                    message="Password not valid.",  # TODO: better message
                    form=request.form,
                )
            session["user"] = user
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
        password = request.form["pw"]
        auth = UserAuthenticator(get_db())
        try:
            auth.authenticate_user(user, password)
        except UserNotFoundError:
            return render_template(
                "pages/login.html", 
                form=request.form,
                message="The requested user was not found.",
            )
        except PasswordMismatchError:
            return render_template(
                "pages/login.html", 
                form=request.form,
                message="Password incorrect.",
            )
        session["user"] = user
        return redirect(url_for("pages.login_success", user=user))    
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

@bp.route("/logout/")
def logout():
    session.pop("user")
    return redirect(url_for("pages.index", disp="user-logged-out"))

@bp.route("/account/")
def account():
    return render_template("pages/account.html")

@bp.route("/delete/")
def delete():
    return render_template("pages/delete.html")

@bp.route("/delete/confirmed/")
def delete_confirmed():
    auth = UserAuthenticator(get_db())
    try:
        auth.delete_user(session["user"])
    except UserNotFoundError:
        return redirect(url_for("pages.error", message="The account has already been deleted."))
    except KeyError:
        return redirect(url_for("pages.error", message="No user logged in."))
    session.pop("user")
    return redirect(url_for("pages.index", disp="account-delete-success"))

@bp.route("/error/")
def error():
    return render_template("pages/error.html", message=request.args["message"])
