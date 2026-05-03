from project.domain.repositories import AbstractOrganizationRepository
from project.domain.types.object_id import ObjectId
from project.models import AdminUnit
from project.models.admin_unit import AdminUnitMember
from project.models.app import AppInstallation
from project.models.oauth import OAuth2Client
from project.models.user import User
from project.models.webhook import Webhook


class SqlAlchemyOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, organization: AdminUnit):  # pragma: no cover
        self.session.add(organization)

    def _get(self, object_id: int) -> AdminUnit:
        return self.session.query(AdminUnit).filter_by(id=object_id).first()

    def _remove(self, organization: AdminUnit):  # pragma: no cover
        self.session.delete(organization)

    def _get_members_with_permission(
        self, organization_id: ObjectId, permission: str
    ) -> list[AdminUnitMember]:
        members: list[AdminUnitMember] = (
            AdminUnitMember.query.join(User)
            .filter(AdminUnitMember.admin_unit_id == organization_id)
            .all()
        )

        return list(filter(lambda member: member.has_permission(permission), members))

    def _get_app_installations_with_webhook(
        self, admin_unit_id: ObjectId, event_type: str
    ) -> list[AppInstallation]:
        return (
            self.session.query(AppInstallation)
            .join(AppInstallation.oauth2_client)
            .join(OAuth2Client.webhook)
            .filter(OAuth2Client.is_app)
            .filter(AppInstallation.admin_unit_id == admin_unit_id)
            .filter(Webhook.url.isnot(None))
            .filter(Webhook.disabled.isnot(True))
            .filter(Webhook.event_types.contains([event_type]))
            .all()
        )
