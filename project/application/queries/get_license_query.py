from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.image_read_model import LicenseRefReadModel
from project.domain.types.object_id import ObjectId


class GetLicenseQuery(Query[Optional[LicenseRefReadModel]]):
    """The license, or `None`."""

    id: ObjectId
