from typing import List

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class ReferenceRequestSuggestionsReadModel(BaseReadModel):
    """Organizations the event create form offers for reference requests. `selected_ids`
    is the preselected subset of `choices`."""

    model_config = ConfigDict(frozen=True)

    choices: List[OrganizationRefReadModel] = []
    selected_ids: List[ObjectId] = []
