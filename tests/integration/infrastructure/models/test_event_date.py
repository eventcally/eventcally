import datetime

import pytest
from sqlalchemy.exc import IntegrityError


def _definition(start, end):
    from project.infrastructure.models import EventDateDefinition

    return EventDateDefinition(start=start, end=end)


def test_validate_start_must_be_before_end(app):
    start = datetime.datetime(2030, 1, 2, tzinfo=datetime.UTC)

    with pytest.raises(IntegrityError) as e:
        _definition(start, start - datetime.timedelta(hours=1)).validate()
    assert e.value.orig.message == "The start must be before the end."


def test_validate_maximum_duration(app):
    start = datetime.datetime(2030, 1, 1, tzinfo=datetime.UTC)

    with pytest.raises(IntegrityError) as e:
        _definition(start, start + datetime.timedelta(days=181)).validate()
    assert e.value.orig.message == "An event can last a maximum of 180 days."

    _definition(start, start + datetime.timedelta(days=180)).validate()
    _definition(start, None).validate()
