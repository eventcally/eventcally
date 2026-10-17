"""Read models of the batch reads (dumps, sitemap, image route)."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.event_read_models import (
    EventOrganizerEmbedReadModel,
)
from project.domain.types.object_id import ObjectId


class DumpOrganizerReadModel(EventOrganizerEmbedReadModel):
    """An organizer as the dump shows it (`OrganizerDumpSchema`)."""

    admin_unit_id: ObjectId


class DumpEventReferenceReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    event_id: ObjectId
    admin_unit_id: ObjectId


class SitemapEventReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    last_modified_at: Optional[datetime] = None


class ImageMetaReadModel(BaseReadModel):
    """What the image route needs to name its cache file."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    encoding_format: Optional[str] = None
    last_modified_at: Optional[datetime] = None

    def get_file_extension(self) -> str:
        return self.encoding_format.split("/")[-1] if self.encoding_format else "png"

    def get_hash(self) -> int:
        if not self.last_modified_at:
            return 0

        return int(
            self.last_modified_at.replace(tzinfo=timezone.utc).timestamp() * 1000
        )


class ImageFileReadModel(BaseReadModel):
    """An image with its bytes (loaded only where they are needed)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    encoding_format: Optional[str] = None
    data: Optional[bytes] = None

    def get_file_extension(self) -> str:
        return self.encoding_format.split("/")[-1] if self.encoding_format else "png"
