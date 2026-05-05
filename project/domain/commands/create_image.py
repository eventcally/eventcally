from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class CreateImage(CustomBaseModel):
    data: bytes
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[int] = None
