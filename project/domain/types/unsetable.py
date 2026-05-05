from typing import Any, TypeVar, Union, get_args

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from typing_extensions import Annotated

from .unset import _Unset

T = TypeVar("T")


class UnsetableAdapter:
    """Pydantic adapter for Unsetable fields."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Get the inner type from Unsetable[T]
        args = get_args(source_type)
        if args and len(args) >= 2:
            # Unsetable = Union[type[_Unset], T, None]
            inner_type = args[1]
            inner_schema = handler.generate_schema(inner_type)
        else:  # pragma: no cover
            inner_schema = core_schema.any_schema()

        def validate(value: Any) -> Any:
            return value

        def serialize(value: Any) -> Any:
            return value

        return core_schema.no_info_before_validator_function(
            validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(_Unset),
                    inner_schema,
                    core_schema.none_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(serialize),
        )


Unsetable = Annotated[Union[type[_Unset], T, None], UnsetableAdapter]
