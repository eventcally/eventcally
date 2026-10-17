"""Tests for UnsetableAdapter and NullableUnsetableAdapter / NullableUnsetable."""

from typing import Union

import pytest
from pydantic import ValidationError

from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset import _Unset, unset
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import (
    NullableUnsetable,
    Unsetable,
    UnsetableAdapter,
)

# ---------------------------------------------------------------------------
# Models that trigger pydantic schema compilation for both adapters
# ---------------------------------------------------------------------------


class _ModelWithUnsetable(CustomBaseModel):
    value: Unsetable[str] = UnsetField()


class _ModelWithNullableUnsetable(CustomBaseModel):
    value: NullableUnsetable[str] = UnsetField()


# ---------------------------------------------------------------------------
# Unsetable (no None allowed)
# ---------------------------------------------------------------------------


class TestUnsetable:
    def test_accepts_string_value(self):
        m = _ModelWithUnsetable(value="hello")
        assert m.value == "hello"

    def test_accepts_unset(self):
        m = _ModelWithUnsetable()
        assert m.value is unset

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            _ModelWithUnsetable(value=None)


# ---------------------------------------------------------------------------
# NullableUnsetable (None allowed — triggers line 21 Union branch)
# ---------------------------------------------------------------------------


class TestNullableUnsetable:
    def test_accepts_string_value(self):
        m = _ModelWithNullableUnsetable(value="hello")
        assert m.value == "hello"

    def test_accepts_none(self):
        m = _ModelWithNullableUnsetable(value=None)
        assert m.value is None

    def test_accepts_unset(self):
        m = _ModelWithNullableUnsetable()
        assert m.value is unset


# ---------------------------------------------------------------------------
# Direct unit tests for _get_inner_type branches
# ---------------------------------------------------------------------------


class TestGetInnerTypeBranches:
    def test_union_source_type_hits_union_branch(self):
        """Trigger line 21: source_type is Annotated[Union[type[_Unset], T, None], ...].
        When get_args returns (Union[...], Adapter), the first arg is Union, so
        union_args = get_args(args[0]) is executed."""
        # Build a fake source_type: Annotated[Union[type[_Unset], str, None], adapter]
        # _get_inner_type receives the outer Annotated type, so pydantic calls it with
        # `source_type = NullableUnsetable[str]` which expands to
        # Annotated[Union[type[_Unset], str, None], NullableUnsetableAdapter].
        # We can reconstruct that manually.
        from typing import Annotated

        from project.domain.types.unsetable import NullableUnsetableAdapter

        source_type = Annotated[
            Union[type[_Unset], str, None], NullableUnsetableAdapter
        ]
        result = NullableUnsetableAdapter._get_inner_type(source_type)
        assert result is str

    def test_no_matching_arg_returns_any(self):
        """Trigger line 29: when all args are _Unset / None, fallback is 'Any'."""
        from typing import Annotated, Any

        # source_type where get_args gives only _Unset and NoneType
        # Use a non-union annotated so it goes through `union_args = args` path
        # and the only non-_Unset/None arg doesn't exist.
        source_type = Annotated[Union[type[_Unset], None], UnsetableAdapter]
        result = UnsetableAdapter._get_inner_type(source_type)
        assert result is Any
