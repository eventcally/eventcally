from datetime import datetime, timezone
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class LicenseRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None


class ImageReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    copyright_text: Optional[str] = None
    last_modified_at: Optional[datetime] = None
    license: Optional[LicenseRefReadModel] = None

    def get_hash(self) -> int:
        """Cache-busting hash for `url_for_image`, as `TrackableMixin.get_hash`."""
        if not self.last_modified_at:
            return 0

        return int(
            self.last_modified_at.replace(tzinfo=timezone.utc).timestamp() * 1000
        )


class ImageEditReadModel(BaseReadModel):
    """Fills `Base64ImageForm`: `process` reads `data`/`encoding_format`, the license
    select formats `id`/`code`/`name`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    data: Optional[bytes] = None
    encoding_format: Optional[str] = None
    copyright_text: Optional[str] = None
    license: Optional[LicenseRefReadModel] = None
