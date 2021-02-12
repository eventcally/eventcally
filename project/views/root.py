import os.path

from flask import redirect, render_template, request, url_for
from flask_babelex import gettext
from markupsafe import Markup

from project import app, dump_path
from project.services.admin import upsert_settings
from project.views.utils import track_analytics


@app.route("/")
def home():
    if "src" in request.args:
        track_analytics("home", "", request.args["src"])
        return redirect(url_for("home"))

    return render_template("home.html")


@app.route("/example")
def example():
    return render_template("example.html")


@app.route("/tos")
def tos():
    title = gettext("Terms of service")
    settings = upsert_settings()
    content = Markup(settings.tos)
    return render_template("legal.html", title=title, content=content)


@app.route("/legal_notice")
def legal_notice():
    title = gettext("Legal notice")
    settings = upsert_settings()
    content = Markup(settings.legal_notice)
    return render_template("legal.html", title=title, content=content)


@app.route("/contact")
def contact():
    title = gettext("Contact")
    settings = upsert_settings()
    content = Markup(settings.contact)
    return render_template("legal.html", title=title, content=content)


@app.route("/privacy")
def privacy():
    title = gettext("Privacy")
    settings = upsert_settings()
    content = Markup(settings.privacy)
    return render_template("legal.html", title=title, content=content)


@app.route("/developer")
def developer():
    file_name = "all.zip"
    all_path = os.path.join(dump_path, file_name)
    dump_file = None

    if os.path.exists(all_path):
        dump_file = {
            "url": url_for("dump_files", path=file_name),
            "size": os.path.getsize(all_path),
            "ctime": os.path.getctime(all_path),
        }
    else:
        print("No file at %s" % all_path)

    return render_template("developer/read.html", dump_file=dump_file)
