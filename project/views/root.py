import json
import os.path

from flask import (
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_babel import gettext
from markupsafe import Markup
from sqlalchemy import text

from project import cache_path, dump_path, robots_txt_file, sitemap_file
from project.extensions import db, limiter
from project.services.admin import upsert_settings
from project.views.main_blueprint import main_bp


@main_bp.route("/")
def home():
    structured_data = json.dumps(
        {
            "@context": "http://schema.org",
            "@type": "WebSite",
            "name": current_app.config["SITE_NAME"],
            "url": url_for("main.home", _external=True),
        }
    )

    settings = upsert_settings()
    content = Markup(settings.start_page) if settings.start_page else None

    return render_template(
        "home.html",
        structured_data=structured_data,
        content=content,
    )


@main_bp.route("/up")
def up():
    from project.celery_init import celery

    with db.engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    if (
        "REDIS_URL" in current_app.config and current_app.config["REDIS_URL"]
    ):  # pragma: no cover
        celery.control.ping()

    if (
        "LIMITER_REDIS_URL" in current_app.config
        and current_app.config["LIMITER_REDIS_URL"]
    ):  # pragma: no cover
        storage = getattr(limiter.storage, "storage", None)
        if hasattr(storage, "ping"):
            storage.ping()

    return "OK"


@main_bp.route("/tos")
def tos():
    title = gettext("Terms of service")
    settings = upsert_settings()

    if not settings.tos:
        abort(404)

    content = Markup(settings.tos)
    return render_template("legal.html", title=title, content=content)


@main_bp.route("/legal_notice")
def legal_notice():
    title = gettext("Legal notice")
    settings = upsert_settings()
    content = Markup(settings.legal_notice)
    return render_template("legal.html", title=title, content=content)


@main_bp.route("/contact")
def contact():
    title = gettext("Contact")
    settings = upsert_settings()
    content = Markup(settings.contact)
    return render_template("legal.html", title=title, content=content)


@main_bp.route("/privacy")
def privacy():
    title = gettext("Privacy")
    settings = upsert_settings()
    content = Markup(settings.privacy)
    return render_template("legal.html", title=title, content=content)


@main_bp.route("/developer")
def developer():
    file_name = "all.zip"
    all_path = os.path.join(dump_path, file_name)
    dump_file = None

    if os.path.exists(all_path):
        dump_file = {
            "url": url_for("main.dump_files", path=file_name),
            "size": os.path.getsize(all_path),
            "ctime": os.path.getctime(all_path),
        }
    else:
        current_app.logger.info("No file at %s" % all_path)

    return render_template("developer/read.html", dump_file=dump_file)


@main_bp.route("/favicon.ico")
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])


@main_bp.route("/robots.txt")
def robots_txt():
    return send_from_directory(cache_path, robots_txt_file)


@main_bp.route("/sitemap.xml")
def sitemap_xml():
    return send_from_directory(cache_path, sitemap_file)
