from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from project.application.queries.list_app_keys_query import ListAppKeysQuery
from project.application.queries.list_app_webhook_deliveries_query import (
    ListAppWebhookDeliveriesQuery,
)
from project.application.queries.list_app_webhook_delivery_attempts_query import (
    ListAppWebhookDeliveryAttemptsQuery,
)
from project.application.queries.list_webhook_deliveries_for_app_query import (
    ListWebhookDeliveriesForAppQuery,
)
from project.application.queries.list_webhook_delivery_attempts_for_app_query import (
    ListWebhookDeliveryAttemptsForAppQuery,
)
from project.application.read_models.app_child_read_models import (
    AppInstallationRefReadModel,
    AppKeyReadModel,
    AppWebhookDeliveryAttemptReadModel,
    AppWebhookDeliveryReadModel,
    WebhookEventRefReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_app_child_read_repository import (
    AbstractAppChildReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
)
from project.models import (
    AdminUnit,
    AppInstallation,
    AppKey,
    OAuth2Client,
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookEvent,
)

_delivery_options = [
    joinedload(WebhookDelivery.webhook_event).load_only(
        WebhookEvent.id, WebhookEvent.event_type, WebhookEvent.timestamp
    ),
    joinedload(WebhookDelivery.app_installation).undefer_group("trackable"),
    joinedload(WebhookDelivery.app_installation)
    .joinedload(AppInstallation.admin_unit)
    .load_only(AdminUnit.id, AdminUnit.name),
]


class SqlAlchemyAppChildReadRepository(AbstractAppChildReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def app_admin_unit_id(self, app_id: ObjectId) -> Optional[ObjectId]:
        return self.session.execute(
            select(OAuth2Client.admin_unit_id).where(OAuth2Client.id == app_id)
        ).scalar_one_or_none()

    def webhook_delivery_admin_unit_id(
        self, webhook_delivery_id: ObjectId
    ) -> Optional[ObjectId]:
        return self.session.execute(
            select(OAuth2Client.admin_unit_id)
            .join(WebhookDelivery, WebhookDelivery.app_id == OAuth2Client.id)
            .where(WebhookDelivery.id == webhook_delivery_id)
        ).scalar_one_or_none()

    def list_app_keys(self, query: ListAppKeysQuery) -> Page[AppKeyReadModel]:
        filters = [AppKey.oauth2_client_id == query.app_id]
        stmt = select(AppKey).where(*filters).order_by(AppKey.id)
        count_stmt = select(AppKey.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_key(row[0])
        )

    def get_app_key(self, object_id: ObjectId) -> Optional[AppKeyReadModel]:
        key = self.session.execute(
            select(AppKey).where(AppKey.id == object_id).options(*audit_options(AppKey))
        ).scalar_one_or_none()
        return (
            _to_key(key).model_copy(update={"audit": to_audit_read_model(key)})
            if key
            else None
        )

    def list_deliveries(
        self, query: ListAppWebhookDeliveriesQuery
    ) -> Page[AppWebhookDeliveryReadModel]:
        filters = [WebhookDelivery.app_id == query.app_id]
        stmt = (
            select(WebhookDelivery, OAuth2Client.admin_unit_id)
            .join(OAuth2Client, WebhookDelivery.app_id == OAuth2Client.id)
            .where(*filters)
            .options(*_delivery_options)
            .order_by(WebhookDelivery.id.desc())
        )
        count_stmt = select(WebhookDelivery.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_delivery)

    def get_delivery(
        self, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryReadModel]:
        row = self.session.execute(
            select(WebhookDelivery, OAuth2Client.admin_unit_id)
            .join(OAuth2Client, WebhookDelivery.app_id == OAuth2Client.id)
            .where(WebhookDelivery.id == object_id)
            .options(*_delivery_options)
        ).one_or_none()
        return _to_delivery(row) if row else None

    def list_deliveries_for_app(
        self, query: ListWebhookDeliveriesForAppQuery
    ) -> Page[AppWebhookDeliveryReadModel]:
        filters = [WebhookDelivery.app_id == query.app_id]
        stmt = (
            select(WebhookDelivery, OAuth2Client.admin_unit_id)
            .join(OAuth2Client, WebhookDelivery.app_id == OAuth2Client.id)
            .join(WebhookDelivery.webhook_event)
            .where(*filters)
            .options(*_delivery_options)
            .order_by(WebhookEvent.timestamp.desc(), WebhookDelivery.id)
        )
        count_stmt = select(WebhookDelivery.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_delivery)

    def get_delivery_for_app(
        self, app_id: ObjectId, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryReadModel]:
        delivery = self.get_delivery(object_id)
        return delivery if delivery and delivery.app_id == app_id else None

    def list_attempts_for_app(
        self, query: ListWebhookDeliveryAttemptsForAppQuery
    ) -> Optional[Page[AppWebhookDeliveryAttemptReadModel]]:
        owned = self.session.execute(
            select(WebhookDelivery.id).where(
                WebhookDelivery.id == query.webhook_delivery_id,
                WebhookDelivery.app_id == query.app_id,
            )
        ).scalar_one_or_none()

        if owned is None:
            return None

        filters = [
            WebhookDeliveryAttempt.webhook_delivery_id == query.webhook_delivery_id
        ]
        stmt = (
            self._attempt_select()
            .where(*filters)
            .order_by(WebhookDeliveryAttempt.start_at.desc(), WebhookDeliveryAttempt.id)
        )
        count_stmt = select(WebhookDeliveryAttempt.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_attempt)

    def list_attempts(
        self, query: ListAppWebhookDeliveryAttemptsQuery
    ) -> Page[AppWebhookDeliveryAttemptReadModel]:
        filters = [
            WebhookDeliveryAttempt.webhook_delivery_id == query.webhook_delivery_id
        ]
        stmt = (
            self._attempt_select().where(*filters).order_by(WebhookDeliveryAttempt.id)
        )
        count_stmt = select(WebhookDeliveryAttempt.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_attempt)

    def get_attempt(
        self, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryAttemptReadModel]:
        row = self.session.execute(
            self._attempt_select().where(WebhookDeliveryAttempt.id == object_id)
        ).one_or_none()
        return _to_attempt(row) if row else None

    def _attempt_select(self):
        return (
            select(
                WebhookDeliveryAttempt,
                WebhookDelivery.app_id,
                OAuth2Client.admin_unit_id,
            )
            .join(
                WebhookDelivery,
                WebhookDeliveryAttempt.webhook_delivery_id == WebhookDelivery.id,
            )
            .join(OAuth2Client, WebhookDelivery.app_id == OAuth2Client.id)
        )


def _to_key(key) -> AppKeyReadModel:
    return AppKeyReadModel(
        id=key.id,
        admin_unit_id=key.admin_unit_id,
        oauth2_client_id=key.oauth2_client_id,
        kid=key.kid,
        checksum=key.checksum,
    )


def _to_delivery(row) -> AppWebhookDeliveryReadModel:
    delivery, admin_unit_id = row
    installation = delivery.app_installation

    return AppWebhookDeliveryReadModel(
        id=delivery.id,
        app_id=delivery.app_id,
        admin_unit_id=admin_unit_id,
        webhook_event=WebhookEventRefReadModel(
            id=delivery.webhook_event.id,
            event_type=delivery.webhook_event.event_type,
            timestamp=delivery.webhook_event.timestamp,
        ),
        app_installation=(
            AppInstallationRefReadModel(
                id=installation.id,
                permissions=list(installation.permissions or []),
                created_at=installation.created_at,
                updated_at=installation.updated_at,
                admin_unit=OrganizationRefReadModel(
                    id=installation.admin_unit.id, name=installation.admin_unit.name
                ),
            )
            if installation
            else None
        ),
    )


def _to_attempt(row) -> AppWebhookDeliveryAttemptReadModel:
    attempt, app_id, admin_unit_id = row

    return AppWebhookDeliveryAttemptReadModel(
        id=attempt.id,
        webhook_delivery_id=attempt.webhook_delivery_id,
        app_id=app_id,
        admin_unit_id=admin_unit_id,
        url=attempt.url,
        status=attempt.status,
        status_code=attempt.status_code,
        start_at=attempt.start_at,
        end_at=attempt.end_at,
    )
