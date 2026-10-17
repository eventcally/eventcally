import os

import PIL
from dependency_injector.wiring import Provide, inject
from flask import request, send_file

from project import img_path
from project.application.queries import GetImageFileQuery, GetImageMetaQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.views.main_blueprint import main_bp
from project.shared.imageutils import get_image_from_bytes
from project.shared.utils import make_dir


@main_bp.route("/image/<int:id>")
@main_bp.route("/image/<int:id>/<hash>")
@inject
def image(id, hash=None, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    image = result_or_404(query_bus.handle(GetImageMetaQuery(id=id)))

    # Dimensions
    width = 500
    height = 500

    if "s" in request.args:
        width = int(request.args["s"])
        height = width

    # Generate file name
    extension = image.get_file_extension()
    hash = image.get_hash()
    file_path = os.path.normpath(
        os.path.join(img_path, f"{id}-{hash}-{width}-{height}.{extension}")
    )

    if not file_path.startswith(img_path):  # pragma: no cover
        return None, 404

    # Load from disk if exists
    if os.path.exists(file_path):
        return send_file(file_path)

    # Save from database to disk
    make_dir(img_path)
    image_file = result_or_404(query_bus.handle(GetImageFileQuery(id=id)))
    img = get_image_from_bytes(image_file.data)
    img.thumbnail((width, height), PIL.Image.Resampling.LANCZOS)
    img.save(file_path)

    # Load from disk
    return send_file(file_path)
