from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId


class ImageValueObject(CustomBaseModel):
    data: bytes
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[ObjectId] = None
