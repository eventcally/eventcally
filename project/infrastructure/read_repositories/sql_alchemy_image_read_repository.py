from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import undefer

from project.application.read_models.batch_read_models import (
    ImageFileReadModel,
    ImageMetaReadModel,
)
from project.application.read_repositories.abstract_image_read_repository import (
    AbstractImageReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.models import Image


class SqlAlchemyImageReadRepository(AbstractImageReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_meta(self, image_id: ObjectId) -> Optional[ImageMetaReadModel]:
        row = self.session.execute(
            select(
                Image.id, Image.encoding_format, Image.created_at, Image.updated_at
            ).where(Image.id == image_id)
        ).one_or_none()

        if row is None:
            return None

        return ImageMetaReadModel(
            id=row.id,
            encoding_format=row.encoding_format,
            last_modified_at=row.updated_at or row.created_at,
        )

    def get_file(self, image_id: ObjectId) -> Optional[ImageFileReadModel]:
        image = self.session.execute(
            select(Image).where(Image.id == image_id).options(undefer(Image.data))
        ).scalar_one_or_none()

        if image is None:
            return None

        return ImageFileReadModel(
            id=image.id, encoding_format=image.encoding_format, data=image.data
        )
