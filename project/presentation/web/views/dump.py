from flask import send_from_directory

from project.presentation.web.views.main_blueprint import main_bp
from project.shared.paths import dump_path


@main_bp.route("/dump/<path:path>")
def dump_files(path):
    return send_from_directory(dump_path, path)
