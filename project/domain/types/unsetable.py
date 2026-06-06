from typing import Any, TypeVar, Union, get_args, get_origin

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from typing_extensions import Annotated

from .unset import _Unset

T = TypeVar("T")


class UnsetableAdapter:
    """Pydantic adapter for Unsetable fields."""

    include_none = False

    @classmethod
    def _get_inner_type(cls, source_type: Any) -> Any:
        args = get_args(source_type)
        if len(args) == 2 and get_origin(args[0]) is Union:
            union_args = get_args(args[0])
        else:
            union_args = args

        for arg in union_args:
            if arg != type[_Unset] and arg is not _Unset and arg is not type(None):
                return arg

        return Any

    @classmethod
    def _build_schema(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        inner_type = cls._get_inner_type(source_type)
        if inner_type is Any:  # pragma: no cover
            inner_schema = core_schema.any_schema()
        else:
            inner_schema = handler.generate_schema(inner_type)

        union_items = [core_schema.is_instance_schema(_Unset), inner_schema]
        if cls.include_none:
            union_items.append(core_schema.none_schema())

        return core_schema.no_info_before_validator_function(
            lambda value: value,
            core_schema.union_schema(union_items),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda value: value
            ),
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return cls._build_schema(source_type, handler)


class NullableUnsetableAdapter(UnsetableAdapter):
    include_none = True


Unsetable = Annotated[Union[type[_Unset], T], UnsetableAdapter]
NullableUnsetable = Annotated[Union[type[_Unset], T, None], NullableUnsetableAdapter]
