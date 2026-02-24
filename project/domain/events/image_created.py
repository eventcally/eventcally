from typing import Optional

from pydantic import BaseModel


class ImageCreated(BaseModel):
    data: bytes
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[int] = None
