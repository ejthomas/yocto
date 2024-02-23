import functools

from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    session,
    g,
)

from yocto.auth import UserAuthenticator
from yocto.address import AddressManager
from yocto.db import get_db
from yocto.lib.exceptions import (
    UsernameInvalidError,
    PasswordInvalidError,
    UserNotFoundError,
    PasswordMismatchError,
    UrlInvalidError,
    UrlExistsError,
)
from yocto.lib.utils import USERNAME_IDENTIFIER, LONG_URL_IDENTIFIER, SHORT_ID_IDENTIFIER

bp = Blueprint("pages", __name__, url_prefix="/pages")

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user")
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        user = db.users.find_one({USERNAME_IDENTIFIER: user_id})
        g.user = user

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("pages.login"))

        return view(**kwargs)

    return wrapped_view

@bp.route("/")
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
    session.clear()
    return redirect(url_for("pages.index", disp="user-logged-out"))

@bp.route("/account/")
@login_required
def account():
    return render_template("pages/account.html")

@bp.route("/delete/")
@login_required
def delete():
    return render_template("pages/delete.html")

@bp.route("/delete/confirmed/")
@login_required
def delete_confirmed():
    auth = UserAuthenticator(get_db())
    auth.delete_user(g.user[USERNAME_IDENTIFIER])
    session.clear()
    return redirect(url_for("pages.index", disp="account-delete-success"))

@bp.route("/error/")
def error():
    return render_template("pages/error.html", message=request.args["message"])

@bp.route("/create/", methods=["POST", "GET"])
@login_required
def create():
    if request.method == "POST":
        long_url = request.form["url"]
        am = AddressManager(get_db())
        short_id = am.generate_short_id()
        try:
            am.store_url_and_id(long_url, short_id, g.user[USERNAME_IDENTIFIER])
        except UrlInvalidError:
            return render_template(
            "pages/create.html",
            form={"url": ""},
            short_url=None,
            message="Input is not a valid web address.",
        )
        except UrlExistsError:
            db = get_db()
            short_id = db.urls.find_one({LONG_URL_IDENTIFIER: long_url})[SHORT_ID_IDENTIFIER]
            return render_template(
                "pages/create.html",
                form={"url": ""},
                short_url=am.compose_shortened_url(url_for("pages.index", _external=True), short_id),
                message=None,
            )
        # UserNotFoundError should be impossible due to login_required decorator
        return render_template(
            "pages/create.html",
            form={"url": ""},
            short_url=am.compose_shortened_url(url_for("pages.index", _external=True), short_id),
            message=None,
        )
    else:
        return render_template(
            "pages/create.html",
            form={"url": ""},
            short_url=None,
            message=None,
        )
    
@bp.route("/my-links/")
@login_required
def my_links():
    am = AddressManager(get_db())
    addresses = am.lookup_user_urls(g.user[USERNAME_IDENTIFIER])
    return render_template(
        "pages/my_links.html", 
        links=[
            {
                "long": address[LONG_URL_IDENTIFIER], 
                "short": am.compose_shortened_url(
                    url_for("pages.index", _external=True), 
                    address[SHORT_ID_IDENTIFIER]
                ) 
            }
            for address in addresses
        ]
    )
    