from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import AfterValidator, AwareDatetime


def _require_named_zone(v: datetime) -> datetime:
    if not isinstance(v.tzinfo, ZoneInfo):
        raise ValueError("datetime must use an IANA timezone")
    return v


NamedZoneDatetime = Annotated[AwareDatetime, AfterValidator(_require_named_zone)]
