from flask import Blueprint, redirect, url_for

bp = Blueprint("short", __name__, url_prefix=None)

@bp.route("/")
def index():
    return redirect(url_for("pages.index"))
