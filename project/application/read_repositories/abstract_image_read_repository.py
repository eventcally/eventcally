import abc
from typing import Optional

from project.application.read_models.batch_read_models import (
    ImageFileReadModel,
    ImageMetaReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractImageReadRepository(abc.ABC):
    @abc.abstractmethod
    def get_meta(
        self, image_id: ObjectId
    ) -> Optional[ImageMetaReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_file(
        self, image_id: ObjectId
    ) -> Optional[ImageFileReadModel]:  # pragma: no cover
        raise NotImplementedError
