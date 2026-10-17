from typing import Optional, Union

from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload, undefer_group

from project.application.queries.list_apps_query import ListAppsQuery
from project.application.queries.list_organization_oauth2_clients_query import (
    ListOrganizationOAuth2ClientsQuery,
)
from project.application.queries.list_user_oauth2_clients_query import (
    ListUserOAuth2ClientsQuery,
)
from project.application.read_models.oauth2_client_read_models import (
    AppReadModel,
    OAuth2ClientReadModel,
    WebhookReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_oauth2_client_read_repository import (
    AbstractOAuth2ClientReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
)
from project.models import AdminUnit, OAuth2Client


class SqlAlchemyOAuth2ClientReadRepository(AbstractOAuth2ClientReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self,
        query: Union[
            ListOrganizationOAuth2ClientsQuery,
            ListUserOAuth2ClientsQuery,
            ListAppsQuery,
        ],
    ) -> Page[OAuth2ClientReadModel]:
        if isinstance(query, ListAppsQuery):
            filters = [
                OAuth2Client.admin_unit_id == query.admin_unit_id,
                OAuth2Client.is_app,
            ]
            options = [undefer_group("detail"), joinedload(OAuth2Client.webhook)]
            to_item = _to_app
        elif isinstance(query, ListOrganizationOAuth2ClientsQuery):
            filters = [
                OAuth2Client.admin_unit_id == query.admin_unit_id,
                OAuth2Client.is_app.is_(False),
            ]
            options = []
            to_item = _to_client
        else:
            filters = [OAuth2Client.user_id == query.user_id]
            options = []
            to_item = _to_client

        stmt = (
            select(OAuth2Client)
            .where(*filters)
            .options(*options)
            .order_by(OAuth2Client.id)
        )
        count_stmt = select(OAuth2Client.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: to_item(row[0])
        )

    def get(self, object_id: ObjectId) -> Optional[OAuth2ClientReadModel]:
        client = self.session.execute(
            select(OAuth2Client)
            .where(OAuth2Client.id == object_id)
            .options(*audit_options(OAuth2Client))
        ).scalar_one_or_none()
        return (
            _to_client(client).model_copy(update={"audit": to_audit_read_model(client)})
            if client
            else None
        )

    def get_app(self, object_id: ObjectId) -> Optional[AppReadModel]:
        app = self.session.execute(
            select(OAuth2Client)
            .where(OAuth2Client.id == object_id, OAuth2Client.is_app)
            .options(
                undefer_group("detail"),
                joinedload(OAuth2Client.webhook),
                *audit_options(OAuth2Client),
            )
        ).scalar_one_or_none()
        return (
            _to_app(app).model_copy(update={"audit": to_audit_read_model(app)})
            if app
            else None
        )


def _client_fields(client) -> dict:
    return dict(
        id=client.id,
        admin_unit_id=client.admin_unit_id,
        user_id=client.user_id,
        client_id=client.client_id,
        client_secret=client.client_secret,
        client_name=client.client_name,
        client_uri=client.client_uri,
        scope=client.scope or "",
        redirect_uris=list(client.redirect_uris or []),
    )


def _to_client(client) -> OAuth2ClientReadModel:
    return OAuth2ClientReadModel(**_client_fields(client))


def _to_app(app) -> AppReadModel:
    webhook = app.webhook

    return AppReadModel(
        **_client_fields(app),
        app_permissions=list(app.app_permissions or []),
        homepage_url=app.homepage_url,
        setup_url=app.setup_url,
        description=app.description,
        webhook=(
            WebhookReadModel(
                url=webhook.url,
                secret=webhook.secret,
                disabled=webhook.disabled,
                event_types=list(webhook.event_types or []),
            )
            if webhook
            else None
        ),
    )
