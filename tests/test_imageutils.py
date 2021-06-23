import pytest


def test_resize_image_to_max():
    import PIL

    from project.imageutils import max_image_size, resize_image_to_max

    image = PIL.Image.new("RGB", (max_image_size + 1, max_image_size + 1))
    resize_image_to_max(image)

    assert image.width == max_image_size
    assert image.height == max_image_size


def test_validate_image_too_small():
    import PIL

    from project.imageutils import min_image_size, validate_image

    image = PIL.Image.new("RGB", (min_image_size - 1, min_image_size - 1))

    with pytest.raises(ValueError) as e:
        validate_image(image)

    assert "too small" in str(e.value)


def test_validate_image_unsupported_format():
    from io import BytesIO

    import PIL

    from project.imageutils import get_image_from_bytes, min_image_size, validate_image

    image = PIL.Image.new("RGB", (min_image_size, min_image_size))
    imgByteArr = BytesIO()
    image.save(imgByteArr, format="TIFF")

    tif_image = get_image_from_bytes(imgByteArr.getvalue())

    with pytest.raises(ValueError) as e:
        validate_image(tif_image)

    assert "not supported" in str(e.value)
