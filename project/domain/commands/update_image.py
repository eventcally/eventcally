from typing import Optional

from pydantic import BaseModel

from project.domain.types import Unsetable, unset


class UpdateImage(BaseModel):
    data: Unsetable[bytes] = unset
    encoding_format: Unsetable[str] = unset
    copyright_text: Unsetable[Optional[str]] = unset
    license_id: Unsetable[Optional[int]] = unset
