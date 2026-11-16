import icalendar
import pytest

from project.presentation.web.ical import ical_single_line, ical_text


class TestIcalText:
    @pytest.mark.parametrize("value", [None, "", "plain text"])
    def test_unchanged(self, value):
        assert ical_text(value) == value

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("a\r\nb", "a\nb"),
            ("Start: 10.00 Uhr\r..", "Start: 10.00 Uhr\n.."),
            ("a\tb\x00c\x1bd\x7f", "a\tbcd"),
        ],
    )
    def test_normalizes(self, value, expected):
        assert ical_text(value) == expected

    def test_serializes_without_bare_cr(self):
        event = icalendar.Event()
        event.add("description", ical_text("x\ry\r\nz"))
        data = event.to_ical()

        assert all(b"\r" not in line for line in data.split(b"\r\n"))
        assert icalendar.Event.from_ical(data)["description"] == "x\ny\nz"


class TestIcalSingleLine:
    @pytest.mark.parametrize("value", [None, "", "Seestr. 1"])
    def test_unchanged(self, value):
        assert ical_single_line(value) == value

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Haus am See\r\nSeestr. 1\r\n\r\n", "Haus am See, Seestr. 1"),
            ("a\rb", "a, b"),
            ('Haus "am" See', "Haus 'am' See"),
        ],
    )
    def test_single_line(self, value, expected):
        assert ical_single_line(value) == expected
