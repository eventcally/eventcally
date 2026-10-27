import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel, ValidationError

from project.domain.types.named_zone_datetime import NamedZoneDatetime

berlin = ZoneInfo("Europe/Berlin")


class Model(BaseModel):
    value: NamedZoneDatetime
    maybe: Optional[NamedZoneDatetime] = None


def test_json_format():
    m = Model(value=datetime.datetime(2026, 10, 26, tzinfo=berlin))
    assert '"value":"2026-10-26T00:00:00+01:00[Europe/Berlin]"' in m.model_dump_json()


@pytest.mark.parametrize(
    "dt",
    [
        datetime.datetime(2026, 1, 5, 12, tzinfo=berlin),
        datetime.datetime(2026, 7, 5, 12, tzinfo=berlin),
        datetime.datetime(2026, 10, 25, 2, 30, fold=0, tzinfo=berlin),
        datetime.datetime(2026, 10, 25, 2, 30, fold=1, tzinfo=berlin),
        datetime.datetime(2026, 3, 29, 3, 0, tzinfo=berlin),
    ],
)
def test_round_trip(dt):
    m = Model(value=dt, maybe=dt)
    restored = Model.model_validate_json(m.model_dump_json())
    for r in (restored.value, restored.maybe):
        assert r == dt
        assert r.tzinfo.key == "Europe/Berlin"
        assert r.utcoffset() == dt.utcoffset()
        assert r.fold == dt.fold


def test_none_round_trips():
    m = Model(value=datetime.datetime(2026, 1, 1, tzinfo=berlin))
    assert Model.model_validate_json(m.model_dump_json()).maybe is None


def test_python_mode_unchanged():
    dt = datetime.datetime(2026, 10, 26, tzinfo=berlin)
    m = Model(value=dt)
    assert m.model_dump()["value"] == dt
    assert isinstance(m.model_dump()["value"], datetime.datetime)
    again = Model.model_validate(m.model_dump(round_trip=True), strict=True)
    assert again.value == dt


def test_plain_offset_rejected():
    with pytest.raises(ValidationError, match="IANA timezone"):
        Model.model_validate_json('{"value": "2026-10-26T00:00:00+01:00"}')


def test_unknown_zone_rejected():
    with pytest.raises(ValidationError, match="unknown IANA timezone"):
        Model.model_validate_json('{"value": "2026-10-26T00:00:00+01:00[Nope/Zone]"}')


def test_invalid_zone_name_rejected():
    with pytest.raises(ValidationError, match="unknown IANA timezone"):
        Model.model_validate_json('{"value": "2026-10-26T00:00:00+01:00[../x]"}')


def test_bracket_without_offset_rejected():
    with pytest.raises(ValidationError, match="UTC offset"):
        Model.model_validate_json('{"value": "2026-10-26T00:00:00[Europe/Berlin]"}')


def test_offset_mismatch_rejected():
    with pytest.raises(ValidationError, match="does not match"):
        Model.model_validate_json(
            '{"value": "2026-10-26T00:00:00+02:00[Europe/Berlin]"}'
        )


def test_closing_bracket_without_opening_is_invalid():
    with pytest.raises(ValidationError):
        Model.model_validate_json('{"value": "nonsense]"}')


def test_zone_without_key_serializes_plain(tmp_path):
    import importlib.resources

    data = importlib.resources.files("tzdata.zoneinfo.Europe").joinpath("Berlin")
    path = tmp_path / "custom"
    path.write_bytes(data.read_bytes())
    with open(path, "rb") as f:
        keyless = ZoneInfo.from_file(f)
    assert keyless.key is None

    dt = datetime.datetime(2026, 10, 26, tzinfo=keyless)
    assert '"value":"2026-10-26T00:00:00+01:00"' in Model(value=dt).model_dump_json()
