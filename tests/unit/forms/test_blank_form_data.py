import pytest

from project.views.modular.base_form import BlankFormData


def test_every_field_reads_as_unset():
    blank = BlankFormData()

    assert blank.name is None
    assert blank.location is None
    assert hasattr(blank, "anything")


def test_dunder_lookups_are_not_swallowed():
    with pytest.raises(AttributeError):
        BlankFormData().__wrapped__
