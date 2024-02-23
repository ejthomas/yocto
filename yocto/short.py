from flask import Blueprint, redirect, url_for

from yocto.address import AddressManager
from yocto.db import get_db
from yocto.lib.exceptions import UrlNotFoundError

bp = Blueprint("short", __name__, url_prefix=None)

@bp.route("/")
@bp.route("/<short_id>")
@bp.route("/<short_id>/")
def index(short_id=None):
    if short_id is None:
        return redirect(url_for("pages.index"))
    else:
        am = AddressManager(get_db())
        try:
            long_url = am.lookup_short_id(short_id)
        except UrlNotFoundError:
            return redirect(url_for("pages.error", message="Sorry, this shortened address is not valid."))
        return redirect(long_url)
