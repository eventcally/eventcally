"""Parity of the reference request suggestions of the event create form.

The expected values were captured from the ORM implementation
(`services.admin_unit.get_admin_unit_suggestions_for_reference_requests`) before it
moved to `ListReferenceRequestSuggestionsQuery`.
"""

from project.application.queries import ListReferenceRequestSuggestionsQuery
from project.domain.models.entities.actor import Actor
from tests.integration.seeder import Seeder


def _suggestions(app, user_id, admin_unit_id):
    with app.app_context():
        suggestions = app.container.cqrs.query_bus().handle(
            ListReferenceRequestSuggestionsQuery(
                admin_unit_id=admin_unit_id, actor=Actor(user_id=user_id)
            )
        )
        return [(c.id, c.name) for c in suggestions.choices], list(
            suggestions.selected_ids
        )


def _create_org(app, db, seeder, user_id, name, allowed=True):
    org_id = seeder.create_admin_unit(user_id, name)
    if not allowed:
        with app.app_context():
            from project.infrastructure.models import AdminUnit

            db.session.get(AdminUnit, org_id).incoming_reference_requests_allowed = (
                False
            )
            db.session.commit()
    return org_id


def test_suggestions_parity_all_steps(client, app, db, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    orgs = {
        name: _create_org(app, db, seeder, other_user_id, name)
        for name in ["R1", "R2", "F1", "A1", "V1", "Plain"]
    }
    forbidden_id = _create_org(app, db, seeder, other_user_id, "Closed", allowed=False)
    event_id = seeder.create_event(admin_unit_id)

    # Step 1: newest outgoing requests first (R2 newer than R1), closed orgs skipped
    seeder.create_reference_request(event_id, orgs["R1"])
    seeder.create_reference_request(event_id, orgs["R2"])
    seeder.create_reference_request(event_id, forbidden_id)
    # Step 2: outgoing references
    seeder.create_reference(event_id, orgs["F1"])
    # Step 3: inbound relations ordered by auto verify, verify
    seeder.create_admin_unit_relation(orgs["V1"], admin_unit_id, verify=True)
    seeder.create_admin_unit_relation(
        orgs["A1"], admin_unit_id, auto_verify_event_reference_requests=True
    )
    seeder.create_admin_unit_relation(forbidden_id, admin_unit_id, verify=True)

    choices, selected_ids = _suggestions(app, user_id, admin_unit_id)

    # Five slots: R2, R1, F1, A1, V1. "Plain" does not fit anymore.
    assert choices == [
        (orgs["R2"], "R2"),
        (orgs["R1"], "R1"),
        (orgs["F1"], "F1"),
        (orgs["A1"], "A1"),
        (orgs["V1"], "V1"),
    ]
    assert selected_ids == [orgs[n] for n in ["R2", "R1", "F1", "A1", "V1"]]


def test_suggestions_parity_fallback_not_selected(client, app, db, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    first_id = _create_org(app, db, seeder, other_user_id, "First")
    second_id = _create_org(app, db, seeder, other_user_id, "Second")
    _create_org(app, db, seeder, other_user_id, "Closed", allowed=False)

    choices, selected_ids = _suggestions(app, user_id, admin_unit_id)

    # The verified seed organization "eventcally" verifies the admin unit through a
    # relation (step 3, selected); the others only fill the free slots (step 4).
    by_name = {name: id for id, name in choices}
    assert by_name.keys() == {"First", "Second", "eventcally"}
    assert by_name["First"] == first_id and by_name["Second"] == second_id
    assert choices[0][1] == "eventcally"
    assert selected_ids == [by_name["eventcally"]]


def test_suggestions_parity_dedup(client, app, db, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    org_id = _create_org(app, db, seeder, other_user_id, "Both")
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_reference_request(event_id, org_id)
    seeder.create_reference(event_id, org_id)
    seeder.create_admin_unit_relation(org_id, admin_unit_id, verify=True)

    choices, selected_ids = _suggestions(app, user_id, admin_unit_id)

    assert choices[0] == (org_id, "Both")
    assert [name for _, name in choices] == ["Both", "eventcally"]
    assert selected_ids == [org_id, choices[1][0]]
