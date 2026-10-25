import pytest


def test_resize_image_to_max():
    import PIL

    from project.shared.imageutils import max_image_size, resize_image_to_max

    image = PIL.Image.new("RGB", (max_image_size + 1, max_image_size + 1))
    resize_image_to_max(image)

    assert image.width == max_image_size
    assert image.height == max_image_size


def test_resize_image_to_min():
    import PIL

    from project.shared.imageutils import min_image_size, resize_image_to_min

    image = PIL.Image.new("RGB", (min_image_size - 1, min_image_size - 1))
    image = resize_image_to_min(image)

    assert image.width == min_image_size
    assert image.height == min_image_size


def test_validate_image_too_small():
    import PIL

    from project.shared.imageutils import min_image_size, validate_image

    image = PIL.Image.new("RGB", (min_image_size - 1, min_image_size - 1))

    with pytest.raises(ValueError) as e:
        validate_image(image)

    assert "too small" in str(e.value)


def test_get_bytes_from_image():
    from io import BytesIO

    import PIL

    from project.shared.imageutils import (
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


def test_data_uri_roundtrip():
    import PIL

    from project.shared.imageutils import (
        get_bytes_from_image,
        get_data_uri_from_bytes,
        get_image_from_base64_str,
        get_mime_type_from_image,
    )

    image = PIL.Image.new("RGB", (4, 4))
    image.format = "PNG"
    data = get_bytes_from_image(image)

    data_uri = get_data_uri_from_bytes(data, "image/png")
    assert data_uri.startswith("data:image/png;base64,")

    loaded = get_image_from_base64_str(data_uri)
    assert loaded.size == (4, 4)
    assert get_mime_type_from_image(loaded) == "image/png"


def test_get_bytes_from_image_unsupported_format_falls_back_to_png():
    import PIL

    from project.shared.imageutils import get_bytes_from_image, get_image_from_bytes

    image = PIL.Image.new("RGB", (4, 4))
    image.format = "BMP"

    assert get_image_from_bytes(get_bytes_from_image(image)).format == "PNG"


def test_get_image_from_url(requests_mock):
    import PIL

    from project.shared.imageutils import get_bytes_from_image, get_image_from_url

    image = PIL.Image.new("RGB", (4, 4))
    image.format = "PNG"
    requests_mock.get("https://example.com/i.png", content=get_bytes_from_image(image))

    assert get_image_from_url("https://example.com/i.png").size == (4, 4)
