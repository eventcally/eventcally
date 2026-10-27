from datetime import datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, PlainSerializer

# JSON has no tzinfo, so a plain ISO string would lose the IANA zone when an event
# travels through Celery (model_dump_json -> model_validate_json). In JSON mode the
# zone is therefore appended in the RFC 9557 style: 2026-10-26T00:00:00+01:00[Europe/Berlin]


def _parse_zone_suffix(v: Any) -> Any:
    if not isinstance(v, str) or not v.endswith("]"):
        return v

    stamp, separator, zone = v[:-1].rpartition("[")
    if not separator:
        return v

    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        raise ValueError("datetime must include a UTC offset")

    try:
        zone_info = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"unknown IANA timezone {zone!r}")

    converted = parsed.astimezone(zone_info)
    if converted.utcoffset() != parsed.utcoffset():
        raise ValueError("UTC offset does not match timezone")
    return converted


def _require_named_zone(v: datetime) -> datetime:
    if not isinstance(v.tzinfo, ZoneInfo):
        raise ValueError("datetime must use an IANA timezone")
    return v


def _serialize_with_zone(v: datetime) -> str:
    key = getattr(v.tzinfo, "key", None)
    if key is None:
        return v.isoformat()
    return f"{v.isoformat()}[{key}]"


NamedZoneDatetime = Annotated[
    AwareDatetime,
    BeforeValidator(_parse_zone_suffix),
    AfterValidator(_require_named_zone),
    PlainSerializer(_serialize_with_zone, when_used="json"),
]
