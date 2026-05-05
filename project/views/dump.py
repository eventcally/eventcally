from flask import send_from_directory

from project import dump_path
from project.views.main_blueprint import main_bp


@main_bp.route("/dump/<path:path>")
def dump_files(path):
    return send_from_directory(dump_path, path)
