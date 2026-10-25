import pytest

from project.presentation.web.jinja_filters import human_file_size


@pytest.mark.parametrize(
    "size,expected",
    [
        (0, "0 bytes"),
        (1023, "1023 bytes"),
        (1024, "1KB"),
        (5 * 1024**2, "5MB"),
        (3 * 1024**3, "3GB"),
        (1024**7, "1ZB"),
    ],
)
def test_human_file_size(size, expected):
    assert human_file_size(size) == expected
