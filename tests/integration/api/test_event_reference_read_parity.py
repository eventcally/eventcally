"""Byte-level parity of the event reference and reference request read endpoints
(snapshot captured on the ORM path, see `tests/integration/api/read_parity.py`)."""

from datetime import datetime

from sqlalchemy import text

from tests.integration.api.read_parity import assert_matches_snapshot, set_trackable


def _seed(app, db, seeder, admin_unit_id):
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    foreign_events = [
        seeder.create_event(other_admin_unit_id, name=f"Fremd {i}") for i in range(3)
    ]
    own_events = [
        seeder.create_event(admin_unit_id, name=f"Eigen {i}") for i in range(3)
    ]

    ids = {
        "incoming": [seeder.create_reference(e, admin_unit_id) for e in foreign_events],
        "outgoing": [
            seeder.create_reference(e, other_admin_unit_id) for e in own_events
        ],
        "requests_in": [
            seeder.create_reference_request(e, admin_unit_id) for e in foreign_events
        ],
        "requests_out": [
            seeder.create_reference_request(e, other_admin_unit_id) for e in own_events
        ],
    }
    stamps = [
        (datetime(2026, 1, 1, 10), datetime(2026, 3, 1, 12)),
        (datetime(2026, 2, 1, 9), None),
        (datetime(2026, 1, 15, 14), datetime(2026, 2, 20, 16)),
    ]

    with app.app_context():
        for table, key in [
            ("eventreference", "incoming"),
            ("eventreference", "outgoing"),
            ("eventreferencerequest", "requests_in"),
            ("eventreferencerequest", "requests_out"),
        ]:
            for object_id, (created_at, updated_at) in zip(ids[key], stamps):
                set_trackable(db, table, object_id, created_at, updated_at)

        db.session.execute(
            text(
                "UPDATE eventreferencerequest SET review_status = 3,"
                " rejection_reason = 2 WHERE id = :id"
            ),
            {"id": ids["requests_out"][0]},
        )
        db.session.execute(
            text("UPDATE eventreference SET rating = 70 WHERE id = :id"),
            {"id": ids["incoming"][0]},
        )
        db.session.commit()

    return ids


def _list_requests(utils, endpoint, admin_unit_id):
    def url(**kwargs):
        return utils.get_url(endpoint, id=admin_unit_id, **kwargs)

    return {
        "": url(),
        "_sort_created_at": url(sort="-created_at"),
        "_sort_updated_at": url(sort="-updated_at"),
        "_sort_last_modified_at": url(sort="-last_modified_at"),
        "_created_at_from": url(created_at_from="2026-01-12T00:00:00"),
        "_created_at_to": url(created_at_to="2026-02-02T00:00:00"),
        "_updated_at_range": url(
            updated_at_from="2026-02-01T00:00:00", updated_at_to="2026-02-28T00:00:00"
        ),
        "_last_modified_at_range": url(
            last_modified_at_from="2026-02-01T00:00:00",
            last_modified_at_to="2026-03-02T00:00:00",
        ),
        "_page_2": url(page=2, per_page=2),
        "_out_of_range": url(page=4, per_page=2),
    }


def test_event_reference_read_payloads_match_snapshot(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access()
    ids = _seed(app, db, seeder, admin_unit_id)

    requests = {}
    for name, endpoint in [
        ("incoming", "api_v1_organization_incoming_event_reference_list"),
        ("outgoing", "api_v1_organization_outgoing_event_reference_list"),
        ("requests_in", "api_v1_organization_incoming_event_reference_request_list"),
        ("requests_out", "api_v1_organization_outgoing_event_reference_request_list"),
    ]:
        for suffix, url in _list_requests(utils, endpoint, admin_unit_id).items():
            requests[f"{name}{suffix}"] = url

    requests.update(
        {
            "reference_detail": utils.get_url(
                "api_v1_event_reference", id=ids["incoming"][0]
            ),
            "reference_detail_foreign": utils.get_url(
                "api_v1_event_reference", id=ids["outgoing"][1]
            ),
            "reference_detail_unknown": utils.get_url(
                "api_v1_event_reference", id=4711
            ),
            "request_detail": utils.get_url(
                "api_v1_event_reference_request", id=ids["requests_out"][0]
            ),
            "request_detail_incoming": utils.get_url(
                "api_v1_event_reference_request", id=ids["requests_in"][0]
            ),
            "request_detail_unknown": utils.get_url(
                "api_v1_event_reference_request", id=4711
            ),
        }
    )

    assert_matches_snapshot("event_reference", utils, requests)
