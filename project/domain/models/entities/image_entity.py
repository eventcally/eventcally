from __future__ import annotations

from typing import Optional

from project.domain.models.entities.base_entity import BaseEntity
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable


class ImageEntity(BaseEntity):
    id: ObjectId
    hash: int
    data: bytes
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[ObjectId] = None

    @classmethod
    def from_value_object(
        cls, image_value_object: Optional[ImageValueObject]
    ) -> Optional[ImageEntity]:
        if image_value_object is None:
            return None

        return cls.model_construct(
            id=-1,
            hash=-1,
            data=image_value_object.data,
            encoding_format=image_value_object.encoding_format,
            copyright_text=image_value_object.copyright_text,
            license_id=image_value_object.license_id,
        )

    @classmethod
    def from_nullable_unsetable_value_object(
        cls, image_value_object: NullableUnsetable[ImageValueObject]
    ) -> NullableUnsetable[ImageEntity]:
        if image_value_object is unset:
            return unset
        return cls.from_value_object(image_value_object)
