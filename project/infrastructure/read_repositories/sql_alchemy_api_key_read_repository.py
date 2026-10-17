from typing import Optional, Union

from sqlalchemy import exists, func, select
from sqlalchemy.orm import undefer_group

from project.application.queries.api_key_sort import ApiKeySort
from project.application.queries.list_organization_api_keys_query import (
    ListOrganizationApiKeysQuery,
)
from project.application.queries.list_user_api_keys_query import ListUserApiKeysQuery
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_api_key_read_repository import (
    AbstractApiKeyReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, ApiKey
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
)

# Default (no or unknown sort key) is the list form's first choice, the name.
_SORT_ORDER = {
    None: [func.lower(ApiKey.name)],
    ApiKeySort.name: [func.lower(ApiKey.name)],
    ApiKeySort.created_at_desc: [ApiKey.created_at.desc()],
}


class SqlAlchemyApiKeyReadRepository(AbstractApiKeyReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: Union[ListOrganizationApiKeysQuery, ListUserApiKeysQuery]
    ) -> Page[ApiKeyReadModel]:
        if isinstance(query, ListOrganizationApiKeysQuery):
            filters = [ApiKey.admin_unit_id == query.admin_unit_id]
        else:
            filters = [ApiKey.user_id == query.user_id]

        stmt = (
            select(ApiKey)
            .where(*filters)
            .options(undefer_group("trackable"))
            .order_by(*_SORT_ORDER[query.sort], ApiKey.id)
        )
        count_stmt = select(ApiKey.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )

    def get(self, object_id: ObjectId) -> Optional[ApiKeyReadModel]:
        api_key = self.session.execute(
            select(ApiKey).where(ApiKey.id == object_id).options(*audit_options(ApiKey))
        ).scalar_one_or_none()
        return (
            _to_model(api_key).model_copy(
                update={"audit": to_audit_read_model(api_key)}
            )
            if api_key
            else None
        )


def _to_model(api_key) -> ApiKeyReadModel:
    return ApiKeyReadModel(
        id=api_key.id,
        name=api_key.name,
        admin_unit_id=api_key.admin_unit_id,
        user_id=api_key.user_id,
        rate_limit_value=api_key.rate_limit_value,
        created_at=api_key.created_at,
    )
