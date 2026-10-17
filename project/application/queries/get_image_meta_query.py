from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import ImageMetaReadModel
from project.domain.types.object_id import ObjectId


class GetImageMetaQuery(Query[Optional[ImageMetaReadModel]]):
    """The image without its bytes, or `None`."""

    id: ObjectId
