from __future__ import annotations

from typing import Optional

from project.domain.models.entities.image_entity import ImageEntity
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId


class ImageForEvent(CustomBaseModel):
    id: ObjectId
    hash: int
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[ObjectId] = None

    @classmethod
    def from_image_entity(cls, image_entity: ImageEntity) -> ImageForEvent:
        if image_entity is None:
            return None

        return cls.model_construct(
            id=image_entity.id,
            hash=image_entity.hash,
            encoding_format=image_entity.encoding_format,
            copyright_text=image_entity.copyright_text,
            license_id=image_entity.license_id,
        )
