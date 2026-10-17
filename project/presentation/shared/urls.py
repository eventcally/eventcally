from flask import url_for


def url_for_image(image, **values):
    return url_for("main.image", id=image.id, hash=image.get_hash(), **values)
