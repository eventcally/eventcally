from typing import Annotated, Optional

from pydantic import AfterValidator


def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _strip_lines(value: str) -> str:
    return "\n".join(line.strip() for line in value.split("\n") if line.strip())


def _empty_to_none(value: Optional[str]) -> Optional[str]:
    return value or None


NormalizedText = Annotated[str, AfterValidator(_normalize_newlines)]
TrimmedText = Annotated[NormalizedText, AfterValidator(str.strip)]
RecurrenceRule = Annotated[NormalizedText, AfterValidator(_strip_lines)]
NullableRecurrenceRule = Annotated[
    Optional[RecurrenceRule], AfterValidator(_empty_to_none)
]
