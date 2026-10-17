"""Byte-level parity of the verification request and relation read endpoints
(snapshot captured on the ORM path, see `tests/integration/api/read_parity.py`)."""

from datetime import datetime

from sqlalchemy import text

from tests.integration.api.read_parity import assert_matches_snapshot, set_trackable

STAMPS = [
    (datetime(2026, 1, 1, 10), datetime(2026, 3, 1, 12)),
    (datetime(2026, 2, 1, 9), None),
    (datetime(2026, 1, 15, 14), datetime(2026, 2, 20, 16)),
]


def _seed(app, db, seeder, admin_unit_id):
    others = [
        seeder.create_admin_unit(seeder.create_user(f"o{i}@test.de"), f"Crew {i}")
        for i in range(3)
    ]
    incoming = [
        seeder.create_admin_unit_verification_request(other, admin_unit_id)
        for other in others
    ]
    outgoing = [
        seeder.create_admin_unit_verification_request(admin_unit_id, other)
        for other in others
    ]
    relations = [
        seeder.create_admin_unit_relation(admin_unit_id, others[2], verify=True),
        seeder.create_admin_unit_relation(
            admin_unit_id, others[0], auto_verify_event_reference_requests=True
        ),
        seeder.create_admin_unit_relation(admin_unit_id, others[1]),
    ]

    with app.app_context():
        for table, ids in [
            ("adminunitverificationrequest", incoming),
            ("adminunitverificationrequest", outgoing),
            ("adminunitrelation", relations),
        ]:
            for object_id, (created_at, updated_at) in zip(ids, STAMPS):
                set_trackable(db, table, object_id, created_at, updated_at)

        db.session.execute(
            text(
                "UPDATE adminunitverificationrequest SET review_status = 3,"
                " rejection_reason = 4 WHERE id = :id"
            ),
            {"id": outgoing[0]},
        )
        db.session.commit()

    return others, incoming, outgoing, relations


def test_verification_relation_read_payloads_match_snapshot(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access()
    others, incoming, outgoing, relations = _seed(app, db, seeder, admin_unit_id)

    requests = {}
    for name, endpoint in [
        (
            "incoming",
            "api_v1_organization_incoming_organization_verification_request_list",
        ),
        (
            "outgoing",
            "api_v1_organization_outgoing_organization_verification_request_list",
        ),
    ]:

        def url(**kwargs):
            return utils.get_url(endpoint, id=admin_unit_id, **kwargs)

        requests.update(
            {
                name: url(),
                f"{name}_sort_updated_at": url(sort="-updated_at"),
                f"{name}_sort_last_modified_at": url(sort="-last_modified_at"),
                f"{name}_created_at_from": url(created_at_from="2026-01-12T00:00:00"),
                f"{name}_updated_at_range": url(
                    updated_at_from="2026-02-01T00:00:00",
                    updated_at_to="2026-02-28T00:00:00",
                ),
                f"{name}_page_2": url(page=2, per_page=2),
                f"{name}_out_of_range": url(page=4, per_page=2),
            }
        )

    requests.update(
        {
            "verification_detail": utils.get_url(
                "api_v1_organization_verification_request", id=outgoing[0]
            ),
            "verification_detail_incoming": utils.get_url(
                "api_v1_organization_verification_request", id=incoming[1]
            ),
            "verification_detail_unknown": utils.get_url(
                "api_v1_organization_verification_request", id=4711
            ),
            "relations": utils.get_url(
                "api_v1_organization_outgoing_relation_list", id=admin_unit_id
            ),
            "relations_page_2": utils.get_url(
                "api_v1_organization_outgoing_relation_list",
                id=admin_unit_id,
                page=2,
                per_page=2,
            ),
            "relation_by_target": utils.get_url(
                "api_v1_organization_outgoing_relation",
                id=admin_unit_id,
                target_id=others[0],
            ),
            "relation_by_unknown_target": utils.get_url(
                "api_v1_organization_outgoing_relation",
                id=admin_unit_id,
                target_id=4711,
            ),
            "relation_detail": utils.get_url(
                "api_v1_organization_relation", id=relations[0]
            ),
            "relation_detail_unknown": utils.get_url(
                "api_v1_organization_relation", id=4711
            ),
        }
    )

    assert_matches_snapshot("verification_relation", utils, requests)
