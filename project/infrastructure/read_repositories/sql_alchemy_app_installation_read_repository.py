from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload, undefer_group

from project.application.queries.list_app_installations_for_app_query import (
    ListAppInstallationsForAppQuery,
)
from project.application.queries.list_app_installations_query import (
    ListAppInstallationsQuery,
)
from project.application.queries.list_user_app_installations_query import (
    ListUserAppInstallationsQuery,
)
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
    InstallableAppReadModel,
    UserAppInstallationReadModel,
)
from project.application.read_models.organization_member_read_models import (
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitMember,
    AppInstallation,
    OAuth2Client,
)
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
    trackable_order,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
    to_organization_ref_read_model,
)

_options = [
    undefer_group("trackable"),
    joinedload(AppInstallation.oauth2_client).undefer_group("detail"),
    joinedload(AppInstallation.admin_unit).load_only(AdminUnit.id, AdminUnit.name),
]


class SqlAlchemyAppInstallationReadRepository(AbstractAppInstallationReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(self, query: ListAppInstallationsQuery) -> Page[AppInstallationReadModel]:
        filters = [AppInstallation.admin_unit_id == query.admin_unit_id]
        stmt = (
            select(AppInstallation)
            .where(*filters)
            .options(*_options)
            .order_by(AppInstallation.id)
        )
        count_stmt = select(AppInstallation.id).where(*filters)
        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: _to_installation(row[0]),
        )

    def get(self, object_id: ObjectId) -> Optional[AppInstallationReadModel]:
        installation = self.session.execute(
            select(AppInstallation)
            .where(AppInstallation.id == object_id)
            .options(*_options, *audit_options(AppInstallation))
        )
        # The self-referential audit relationships are mapped as collections.
        installation = installation.unique().scalar_one_or_none()

        if installation is None:
            return None

        return _to_installation(installation).model_copy(
            update={"audit": to_audit_read_model(installation)}
        )

    def get_installable_app(
        self, object_id: ObjectId
    ) -> Optional[InstallableAppReadModel]:
        app = self.session.execute(
            select(OAuth2Client)
            .where(OAuth2Client.id == object_id, OAuth2Client.is_app)
            .options(undefer_group("detail"))
        ).scalar_one_or_none()
        return _to_app(app) if app else None

    def list_for_app(
        self, query: ListAppInstallationsForAppQuery
    ) -> Page[AppInstallationReadModel]:
        filters = [
            AppInstallation.oauth2_client_id == query.app_id,
            *trackable_filters(AppInstallation, query.trackable),
        ]
        stmt = (
            select(AppInstallation)
            .where(*filters)
            .options(*_options)
            .order_by(*trackable_order(AppInstallation, query.sort), AppInstallation.id)
        )
        count_stmt = select(AppInstallation.id).where(*filters)
        return paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: _to_installation(row[0]),
        )

    def get_for_app(
        self, app_id: ObjectId, object_id: ObjectId
    ) -> Optional[AppInstallationReadModel]:
        installation = self.session.execute(
            select(AppInstallation)
            .where(
                AppInstallation.id == object_id,
                AppInstallation.oauth2_client_id == app_id,
            )
            .options(*_options)
        ).scalar_one_or_none()
        return _to_installation(installation) if installation else None

    def list_for_user(
        self, query: ListUserAppInstallationsQuery
    ) -> Page[UserAppInstallationReadModel]:
        membership = [
            AdminUnitMember.admin_unit_id == AppInstallation.admin_unit_id,
            AdminUnitMember.user_id == query.user_id,
        ]

        if query.admin_only:
            membership.append(AdminUnitMember.is_admin)

        filters = [
            AppInstallation.oauth2_client_id == query.app_id,
            exists().where(*membership),
        ]
        stmt = (
            select(AppInstallation)
            .where(*filters)
            .options(
                joinedload(AppInstallation.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                )
            )
            .order_by(AppInstallation.id)
        )
        count_stmt = select(AppInstallation.id).where(*filters)
        page = paginate(
            self.session,
            stmt,
            count_stmt,
            query.page,
            lambda row: UserAppInstallationReadModel(
                id=row[0].id,
                admin_unit_id=row[0].admin_unit_id,
                admin_unit=to_organization_ref_read_model(row[0].admin_unit),
            ),
        )
        memberships = self._memberships(
            query.user_id, [item.admin_unit_id for item in page.items]
        )
        return page.model_copy(
            update={
                "items": [
                    item.model_copy(
                        update={"membership": memberships.get(item.admin_unit_id)}
                    )
                    for item in page.items
                ]
            }
        )

    def _memberships(self, user_id, admin_unit_ids) -> dict:
        rows = self.session.execute(
            select(AdminUnitMember, AdminUnitMember.is_admin)
            .where(
                AdminUnitMember.user_id == user_id,
                AdminUnitMember.admin_unit_id.in_(admin_unit_ids),
            )
            .options(
                joinedload(AdminUnitMember.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                )
            )
        ).all()
        return {
            member.admin_unit_id: UserOrganizationMembershipReadModel(
                id=member.id,
                admin_unit_id=member.admin_unit_id,
                user_id=member.user_id,
                is_admin=bool(is_admin),
                admin_unit=to_organization_ref_read_model(member.admin_unit),
            )
            for member, is_admin in rows
        }


def _to_app(app) -> InstallableAppReadModel:
    return InstallableAppReadModel(
        id=app.id,
        client_name=app.client_name,
        homepage_url=app.homepage_url,
        setup_url=app.setup_url,
        description=app.description,
        app_permissions=list(app.app_permissions or []),
    )


def _to_installation(installation) -> AppInstallationReadModel:
    return AppInstallationReadModel(
        id=installation.id,
        admin_unit_id=installation.admin_unit_id,
        oauth2_client_id=installation.oauth2_client_id,
        permissions=list(installation.permissions or []),
        created_at=installation.created_at,
        updated_at=installation.updated_at,
        admin_unit=to_organization_ref_read_model(installation.admin_unit),
        oauth2_client=_to_app(installation.oauth2_client),
    )
