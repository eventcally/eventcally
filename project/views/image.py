import os
from io import BytesIO

import PIL
from flask import request, send_file
from sqlalchemy.orm import load_only

from project import app, img_path
from project.models import Image
from project.utils import make_dir


@app.route("/image/<int:id>")
def image(id):
    image = Image.query.options(load_only(Image.id, Image.encoding_format)).get_or_404(
        id
    )

    # Dimensions
    width = 500
    height = 500

    if "s" in request.args:
        width = int(request.args["s"])
        height = width
    elif "w" in request.args:
        width = int(request.args["w"])
    elif "h" in request.args:
        height = int(request.args["h"])

    # Generate file name
    extension = image.encoding_format.split("/")[-1] if image.encoding_format else "png"
    file_path = os.path.join(img_path, f"{id}-{width}-{height}.{extension}")

    # Load from disk if exists
    if os.path.exists(file_path):
        return send_file(file_path)

    # Save from database to disk
    make_dir(img_path)
    img = PIL.Image.open(BytesIO(image.data))
    img.thumbnail((width, height), PIL.Image.ANTIALIAS)
    img.save(file_path)

    # Load from disk
    return send_file(file_path)
