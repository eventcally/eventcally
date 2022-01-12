import pytest


def test_resize_image_to_max():
    import PIL

    from project.imageutils import max_image_size, resize_image_to_max

    image = PIL.Image.new("RGB", (max_image_size + 1, max_image_size + 1))
    resize_image_to_max(image)

    assert image.width == max_image_size
    assert image.height == max_image_size


def test_resize_image_to_min():
    import PIL

    from project.imageutils import min_image_size, resize_image_to_min

    image = PIL.Image.new("RGB", (min_image_size - 1, min_image_size - 1))
    image = resize_image_to_min(image)

    assert image.width == min_image_size
    assert image.height == min_image_size


def test_validate_image_too_small():
    import PIL

    from project.imageutils import min_image_size, validate_image

    image = PIL.Image.new("RGB", (min_image_size - 1, min_image_size - 1))

    with pytest.raises(ValueError) as e:
        validate_image(image)

    assert "too small" in str(e.value)


def test_get_bytes_from_image():
    from io import BytesIO

    import PIL

    from project.imageutils import (
        get_bytes_from_image,
        get_image_from_bytes,
        min_image_size,
    )

    image = PIL.Image.new("RGB", (min_image_size, min_image_size))
    imgByteArr = BytesIO()
    image.save(imgByteArr, format="TIFF")

    tif_image = get_image_from_bytes(imgByteArr.getvalue())

    new_bytes = get_bytes_from_image(tif_image)
    new_image = get_image_from_bytes(new_bytes)

    assert new_image.format.lower() == "png"
