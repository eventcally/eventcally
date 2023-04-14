import os

import PIL
from flask import request, send_file
from sqlalchemy.orm import load_only

from project import app, img_path
from project.imageutils import get_image_from_bytes
from project.models import Image
from project.utils import make_dir


@app.route("/image/<int:id>")
@app.route("/image/<int:id>/<hash>")
def image(id, hash=None):
    image = Image.query.options(
        load_only(Image.id, Image.encoding_format, Image.updated_at)
    ).get_or_404(id)

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
    img = get_image_from_bytes(image.data)
    img.thumbnail((width, height), PIL.Image.ANTIALIAS)
    img.save(file_path)

    # Load from disk
    return send_file(file_path)
