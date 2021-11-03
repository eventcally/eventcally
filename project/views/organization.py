from flask import render_template

from project import app


@app.route("/organizations")
@app.route("/organizations/<path:path>")
def organizations(path=None):
    return render_template("organization/main.html")
