import shutil

import pytest

from project import img_path


@pytest.mark.parametrize("size", [None, 100])
@pytest.mark.parametrize("width", [None, 100])
@pytest.mark.parametrize("height", [None, 100])
def test_read(app, seeder, utils, size, width, height):
    user_id, admin_unit_id = seeder.setup_base()
    image_id = seeder.upsert_default_image()

    shutil.rmtree(img_path, ignore_errors=True)

    url = utils.get_url("image", id=image_id, s=size, w=width, h=height)
    utils.get_ok(url)
    utils.get_ok(url)  # cache
