import pytest
from pydantic import TypeAdapter

from project.domain.types.text import (
    NormalizedText,
    NullableRecurrenceRule,
    TrimmedText,
)

RULE = "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504"


class TestNormalizedText:
    def test_normalizes_newlines_and_keeps_spaces(self):
        adapter = TypeAdapter(NormalizedText)
        assert adapter.validate_python(" a\r\nb\rc ") == " a\nb\nc "


class TestTrimmedText:
    def test_normalizes_and_trims(self):
        assert TypeAdapter(TrimmedText).validate_python(" a\r\n ") == "a"


class TestNullableRecurrenceRule:
    @pytest.mark.parametrize(
        "value",
        [
            RULE,
            RULE.replace("\n", "\r\n"),
            RULE.replace("\n", "\r"),
            "  RRULE:FREQ=WEEKLY;COUNT=5 \r\n EXDATE:20260504  ",
            RULE + "\r\n\r\n",
        ],
    )
    def test_variants_normalize_to_same_rule(self, value):
        assert TypeAdapter(NullableRecurrenceRule).validate_python(value) == RULE

    @pytest.mark.parametrize("value", ["", "  \r\n", None])
    def test_empty_becomes_none(self, value):
        assert TypeAdapter(NullableRecurrenceRule).validate_python(value) is None
