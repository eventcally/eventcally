from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId


class ImageCreated(CustomBaseModel):
    id: ObjectId
    hash: int
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[int] = None
