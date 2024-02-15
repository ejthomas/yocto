from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
@bp.route("/index/")
def index():
    return render_template("pages/index.html")