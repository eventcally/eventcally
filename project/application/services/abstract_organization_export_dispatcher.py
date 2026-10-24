import abc

from project.domain.types import ObjectId


class AbstractOrganizationExportDispatcher(abc.ABC):
    @abc.abstractmethod
    def start(self, admin_unit_id: ObjectId, job_id: str) -> bool:  # pragma: no cover
        """Starts the export as job `job_id`. False if it already ran eagerly and
        there is nothing to track."""
        raise NotImplementedError
