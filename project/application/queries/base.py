from typing import Generic, Optional, TypeVar

from project.domain.models.entities.actor import Actor
from project.domain.types.custom_base_model import CustomBaseModel

QueryResultType = TypeVar("QueryResultType")


class Query(CustomBaseModel, Generic[QueryResultType]):
    """Base class for read requests dispatched through the QueryBus.

    Unlike Command, `actor` is optional: callers construct queries without it and
    the bus fills in the current actor. The type parameter documents the result.
    """

    actor: Optional[Actor] = None
