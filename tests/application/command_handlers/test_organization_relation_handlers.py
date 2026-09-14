"""Unit tests for organization relation command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_organization_relation_handler import (
    CreateOrganizationRelationHandler,
)
from project.application.command_handlers.delete_organization_relation_handler import (
    DeleteOrganizationRelationHandler,
)
from project.application.command_handlers.update_organization_relation_handler import (
    UpdateOrganizationRelationHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission

# ---------------------------------------------------------------------------
# CreateOrganizationRelationHandler
# ---------------------------------------------------------------------------


class TestCreateOrganizationRelationHandler:
    def test_creates_relation_and_returns_result(self, uow):
        grant_permission(uow, 1, "outgoing_organization_relations:write")
        cmd = commands.CreateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
            verify=True,
        )

        result = CreateOrganizationRelationHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.organization_relations.get(result.id)
        assert created is not None
        assert created.source_admin_unit_id == 1
        assert created.target_admin_unit_id == 2
        assert created.auto_verify_event_reference_requests is True
        assert created.verify is True

    def test_settings_round_trips_through_strict_validation(self, uow):
        grant_permission(uow, 1, "outgoing_organization_relations:write")
        cmd = commands.CreateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
        )
        cmd.model_validate(cmd.model_dump(round_trip=True), strict=True)

        result = CreateOrganizationRelationHandler().handle(cmd, uow)

        assert result.id > 0

    def test_self_reference_raises_constraint_error(self, uow):
        grant_permission(uow, 1, "outgoing_organization_relations:write")
        cmd = commands.CreateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=1,
        )

        with pytest.raises(ConstraintError):
            CreateOrganizationRelationHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
        )

        with pytest.raises(UnauthorizedError):
            CreateOrganizationRelationHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateOrganizationRelationHandler
# ---------------------------------------------------------------------------


class TestUpdateOrganizationRelationHandler:
    def _seed(self, uow):
        relation = OrganizationRelationAggregate.create(
            actor=Actor(),
            source_admin_unit_id=1,
            target_admin_unit_id=2,
        )
        uow.organization_relations.add(relation)
        return relation

    def test_updates_auto_verify_event_reference_requests(self, uow):
        relation = self._seed(uow)
        grant_permission(uow, 1, "outgoing_organization_relations:write")
        cmd = commands.UpdateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            id=relation.id,
            auto_verify_event_reference_requests=True,
        )

        UpdateOrganizationRelationHandler().handle(cmd, uow)

        updated = uow.organization_relations.get(relation.id)
        assert updated.auto_verify_event_reference_requests is True
        assert updated.verify is False

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateOrganizationRelationCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateOrganizationRelationHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        relation = self._seed(uow)
        cmd = commands.UpdateOrganizationRelationCommand.model_construct(
            actor=ACTOR,
            id=relation.id,
            auto_verify_event_reference_requests=True,
        )

        with pytest.raises(UnauthorizedError):
            UpdateOrganizationRelationHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteOrganizationRelationHandler
# ---------------------------------------------------------------------------


class TestDeleteOrganizationRelationHandler:
    def _seed(self, uow):
        relation = OrganizationRelationAggregate.create(
            actor=Actor(),
            source_admin_unit_id=1,
            target_admin_unit_id=2,
        )
        uow.organization_relations.add(relation)
        return relation

    def test_removes_relation(self, uow):
        relation = self._seed(uow)
        relation_id = relation.id
        grant_permission(uow, 1, "outgoing_organization_relations:write")

        cmd = commands.DeleteOrganizationRelationCommand.model_construct(
            actor=ACTOR, id=relation_id
        )
        DeleteOrganizationRelationHandler().handle(cmd, uow)

        assert uow.organization_relations.get(relation_id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteOrganizationRelationCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            DeleteOrganizationRelationHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        relation = self._seed(uow)
        cmd = commands.DeleteOrganizationRelationCommand.model_construct(
            actor=ACTOR, id=relation.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteOrganizationRelationHandler().handle(cmd, uow)
