from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import ImageFileReadModel
from project.domain.types.object_id import ObjectId


class GetImageFileQuery(Query[Optional[ImageFileReadModel]]):
    """The image with its bytes, or `None`."""

    id: ObjectId
