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


def test_env_override_reads_the_environment(monkeypatch):
    # Jinja folds `False | env_override(...)` in layout.html when it compiles the
    # template, once per process, so only a direct call covers this on every slice.
    from project.presentation.web.jinja_filters import env_override

    monkeypatch.delenv("EVENTCALLY_TEST_FLAG", raising=False)
    assert env_override("default", "EVENTCALLY_TEST_FLAG") == "default"

    monkeypatch.setenv("EVENTCALLY_TEST_FLAG", "1")
    assert env_override("default", "EVENTCALLY_TEST_FLAG") == "1"
