from project import app, dump_path
from flask import send_from_directory


@app.route("/dump/<path:path>")
def dump_files(path):
    return send_from_directory(dump_path, path)
