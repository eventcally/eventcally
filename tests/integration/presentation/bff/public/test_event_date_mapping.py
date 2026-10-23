import pytest

from project.presentation.bff.public.event_date_mapping import description_preview


def test_description_preview_truncates_at_word_boundary():
    text = " ".join(["wort"] * 100)

    preview = description_preview(f"<p>{text}</p>")

    assert len(preview) <= 200
    assert preview.endswith("wort…")


@pytest.mark.parametrize("value", [None, "", "<p> </p>"])
def test_description_preview_empty(value):
    assert description_preview(value) is None


def test_description_preview_short_text_is_unchanged():
    assert description_preview("a &amp; b") == "a & b"
