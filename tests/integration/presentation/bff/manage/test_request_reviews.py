import pytest
from sqlalchemy import text

REFERENCE_URL = "/bff/manage/organizations/{}/incoming-event-reference-requests/{}"
VERIFICATION_URL = "/bff/manage/organizations/{}/incoming-verification-requests/{}"


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _reference_request(app, db, request_id):
    with app.app_context():
        from project.infrastructure.models import EventReferenceRequest

        request = db.session.get(EventReferenceRequest, request_id)
        return request.review_status.name, request.rejection_reason


def _verification_request(app, db, request_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest

        request = db.session.get(AdminUnitVerificationRequest, request_id)
        return request.review_status.name, request.rejection_reason


def _relation(app, source_id, target_id):
    with app.app_context():
        from project.infrastructure.seed_helpers import get_admin_unit_relation

        relation = get_admin_unit_relation(source_id, target_id)
        return relation and dict(
            verify=relation.verify,
            auto_verify=relation.auto_verify_event_reference_requests,
        )


# reference requests


@pytest.fixture
def reference(client, seeder, utils):
    """The reviewer's organization with one incoming reference request."""
    _, admin_unit_id = seeder.setup_base()
    other_user_id, other_admin_unit_id, event_id, request_id = (
        seeder.create_incoming_reference_request(admin_unit_id)
    )
    # The shell carries the CSRF token for the writes.
    utils.get_ok(
        f"/manage/admin_unit/{admin_unit_id}/incoming_event_reference_request/{request_id}/review"
    )
    return dict(
        admin_unit_id=admin_unit_id,
        other_admin_unit_id=other_admin_unit_id,
        event_id=event_id,
        request_id=request_id,
        url=REFERENCE_URL.format(admin_unit_id, request_id),
    )


def test_reference_anonymous_is_401(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    utils.logout()
    url = REFERENCE_URL.format(admin_unit_id, 1)

    assert utils.get_json(f"{url}/review").status_code == 401
    assert utils.post_json(f"{url}/verify", {}).status_code == 401
    assert utils.post_json(f"{url}/reject", {}).status_code == 401


def test_reference_member_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Reviewer")
    _, _, _, request_id = seeder.create_incoming_reference_request(admin_unit_id)
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    # Any Vue 3 shell carries the CSRF token for the writes.
    utils.get_ok("/organizations")
    url = REFERENCE_URL.format(admin_unit_id, request_id)

    assert utils.get_json(f"{url}/review").status_code == 403
    assert utils.post_json(f"{url}/verify", {}).status_code == 403
    assert utils.post_json(f"{url}/reject", {}).status_code == 403


def test_reference_write_requires_csrf(client, seeder):
    _, admin_unit_id = seeder.setup_base()
    _, _, _, request_id = seeder.create_incoming_reference_request(admin_unit_id)

    response = client.post(
        f"{REFERENCE_URL.format(admin_unit_id, request_id)}/verify", json={}
    )

    assert response.status_code == 400


def test_reference_unknown_request_is_404(client, utils, reference):
    url = REFERENCE_URL.format(reference["admin_unit_id"], 4711)

    assert utils.get_json(f"{url}/review").status_code == 404
    assert utils.post_json(f"{url}/verify", {}).status_code == 404
    assert utils.post_json(f"{url}/reject", {}).status_code == 404


def test_reference_request_of_another_organization_is_404(
    client, app, db, seeder, utils, reference
):
    second_id = seeder.create_admin_unit(_user_id(app), "Second Crew")
    url = REFERENCE_URL.format(second_id, reference["request_id"])

    assert utils.get_json(f"{url}/review").status_code == 404
    assert utils.post_json(f"{url}/verify", {}).status_code == 404
    assert utils.post_json(f"{url}/reject", {}).status_code == 404
    assert _reference_request(app, db, reference["request_id"])[0] == "inbox"


def _user_id(app):
    with app.app_context():
        from project.infrastructure.user_datastore import find_user_by_email

        return find_user_by_email("test@test.de").id


def test_reference_get_review(client, utils, reference):
    review = utils.get_json_ok(f"{reference['url']}/review").json

    assert review["id"] == reference["request_id"]
    assert review["review_status"] == "inbox"
    assert review["event"]["id"] == reference["event_id"]
    assert review["event"]["name"] == "Name"
    assert review["event"]["organization"]["name"] == "Other Crew"
    assert review["event"]["report_url"] == f"/event/{reference['event_id']}/report"
    assert review["event"]["start"] is not None
    assert len(review["dates"]) == 1
    assert review["auto_verify"] is False
    assert "Other Crew" in review["auto_verify_description"]
    assert review["default_rating"] == 50
    assert [c["value"] for c in review["rating_choices"]] == list(range(0, 101, 10))
    assert review["rating_choices"][5]["label"] == "5 (Standard)"
    assert [(c["value"], c["label"]) for c in review["rejection_reasons"]] == [
        (0, "Ohne Grund"),
        (1, "Duplikat"),
        (2, "Unseriös"),
        (4, "Nicht relevant"),
        (3, "Unzulässig"),
    ]
    assert review["list_url"] == (
        f"/manage/admin_unit/{reference['admin_unit_id']}/incoming_event_reference_requests"
    )


def test_reference_get_review_with_a_populated_event(
    client, app, db, seeder, utils, reference
):
    event_id = reference["event_id"]
    image_id = seeder.upsert_default_image()
    place_id = seeder.upsert_event_place(reference["other_admin_unit_id"], "Halle")

    with app.app_context():
        from project.infrastructure.models import Event

        event = db.session.get(Event, event_id)
        event.photo_id = image_id
        event.event_place_id = place_id
        event.price_info = "5 EUR"
        event.tags = "a,b"
        event.kid_friendly = True
        event.age_from = 6
        event.attendance_mode = 3
        event.target_group_origin = 2
        event.status = 2
        event.expected_participants = 120
        event.admin_unit.url = "https://crew.example"
        event.admin_unit.fax = "0456"
        db.session.commit()

    review = utils.get_json_ok(f"{reference['url']}/review").json["event"]

    assert review["photo_url"].startswith("/image/")
    assert review["price_info"] == "5 EUR"
    assert review["tags"] == "a,b"
    assert review["kid_friendly"] is True
    assert review["age_from"] == 6
    assert review["attendance_mode"] == "mixed"
    assert review["attendance_mode_label"] is not None
    assert review["target_group_origin_label"] is not None
    assert review["status"] == "cancelled"
    assert review["status_label"] is not None
    assert review["expected_participants"] == 120
    assert review["place"]["name"] == "Halle"
    assert review["place"]["directions_url"].startswith("http://www.google.com/maps?q=")
    assert "Halle" in review["place"]["directions_url"]
    assert review["organization"]["url"] == "https://crew.example"
    assert review["organization"]["fax"] == "0456"


def test_reference_get_review_hides_default_enum_labels(client, utils, reference):
    event = utils.get_json_ok(f"{reference['url']}/review").json["event"]

    assert event["status_label"] is None
    assert event["target_group_origin_label"] is None
    assert event["attendance_mode_label"] is None
    assert event["place"] is None or event["place"]["directions_url"] is None


def test_reference_verify(client, app, db, utils, reference):
    response = utils.post_json(
        f"{reference['url']}/verify", {"rating": 60, "auto_verify": True}
    )

    assert response.status_code == 200
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{reference['admin_unit_id']}/incoming_event_reference_requests"
    )
    assert _flashes(client) == [("success", "Empfehlung erfolgreich erstellt")]

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "other@test.de"

    with app.app_context():
        from project.infrastructure.models import EventReference

        reference_request = _reference_request(app, db, reference["request_id"])
        assert reference_request[0] == "verified"

        created = db.session.get(EventReference, reference["request_id"])
        assert created.event_id == reference["event_id"]
        assert created.admin_unit_id == reference["admin_unit_id"]
        assert created.rating == 60

    relation = _relation(
        app, reference["admin_unit_id"], reference["other_admin_unit_id"]
    )
    assert relation is not None
    assert relation["auto_verify"]


def test_reference_verify_defaults(client, app, db, utils, reference):
    response = utils.post_json(f"{reference['url']}/verify", {})

    assert response.status_code == 200
    with app.app_context():
        from project.infrastructure.models import EventReference

        assert db.session.get(EventReference, reference["request_id"]).rating == 50

    assert (
        _relation(app, reference["admin_unit_id"], reference["other_admin_unit_id"])
        is None
    )


def test_reference_verify_db_error(client, app, db, mocker, utils, reference):
    utils.mock_db_commit(mocker)

    response = utils.post_json(f"{reference['url']}/verify", {"rating": 50})

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_reference_verify_twice_is_400(client, app, db, utils, reference):
    assert utils.post_json(f"{reference['url']}/verify", {}).status_code == 200

    response = utils.post_json(f"{reference['url']}/verify", {})

    assert response.status_code == 400
    assert response.json["message"]


def test_reference_verify_with_unoffered_rating_is_422(
    client, app, db, utils, reference
):
    for rating in (55, -10, 110):
        response = utils.post_json(f"{reference['url']}/verify", {"rating": rating})
        assert response.status_code == 422

    assert _reference_request(app, db, reference["request_id"])[0] == "inbox"


def test_reference_reject_without_reason(client, app, db, utils, reference):
    response = utils.post_json(f"{reference['url']}/reject", {"rejection_reason": 0})

    assert response.status_code == 200
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{reference['admin_unit_id']}/incoming_event_reference_requests"
    )
    assert _flashes(client) == [
        ("success", "Empfehlungsanfrage erfolgreich aktualisiert")
    ]
    assert _reference_request(app, db, reference["request_id"]) == ("rejected", None)


def test_reference_reject_with_reason(client, app, db, utils, reference):
    response = utils.post_json(f"{reference['url']}/reject", {"rejection_reason": 4})

    assert response.status_code == 200
    status, reason = _reference_request(app, db, reference["request_id"])
    assert status == "rejected"
    assert reason.name == "irrelevant"


def test_reference_reject_with_null_reason(client, app, db, utils, reference):
    response = utils.post_json(f"{reference['url']}/reject", {})

    assert response.status_code == 200
    assert _reference_request(app, db, reference["request_id"]) == ("rejected", None)


def test_reference_reject_with_unknown_reason_is_422(client, app, db, utils, reference):
    response = utils.post_json(f"{reference['url']}/reject", {"rejection_reason": 99})

    assert response.status_code == 422
    assert _reference_request(app, db, reference["request_id"])[0] == "inbox"


# verification requests


@pytest.fixture
def verification(client, seeder, utils, app, db):
    """The verifier's organization with one incoming verification request."""
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    utils.get_ok(
        f"/manage/admin_unit/{verifier_admin_unit_id}/incoming_organization_verification_request/{request_id}/review"
    )
    return dict(
        admin_unit_id=verifier_admin_unit_id,
        source_admin_unit_id=unverified_admin_unit_id,
        request_id=request_id,
        url=VERIFICATION_URL.format(verifier_admin_unit_id, request_id),
    )


def test_verification_anonymous_is_401(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    utils.logout()
    url = VERIFICATION_URL.format(admin_unit_id, 1)

    assert utils.get_json(f"{url}/review").status_code == 401
    assert utils.post_json(f"{url}/approve", {}).status_code == 401
    assert utils.post_json(f"{url}/reject", {}).status_code == 401


def test_verification_member_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(
        owner_id,
        "Verifier",
        verified=True,
        can_verify_other=True,
        incoming_verification_requests_allowed=True,
    )
    _, _, request_id = seeder.create_incoming_admin_unit_verification_request(
        admin_unit_id
    )
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")
    url = VERIFICATION_URL.format(admin_unit_id, request_id)

    assert utils.get_json(f"{url}/review").status_code == 403
    assert utils.post_json(f"{url}/approve", {}).status_code == 403
    assert utils.post_json(f"{url}/reject", {}).status_code == 403


def test_verification_unknown_request_is_404(client, utils, verification):
    url = VERIFICATION_URL.format(verification["admin_unit_id"], 4711)

    assert utils.get_json(f"{url}/review").status_code == 404
    assert utils.post_json(f"{url}/approve", {}).status_code == 404
    assert utils.post_json(f"{url}/reject", {}).status_code == 404


def test_verification_request_of_another_organization_is_404(
    client, app, db, seeder, utils, verification
):
    second_id = seeder.create_admin_unit(_user_id(app), "Second Crew")
    url = VERIFICATION_URL.format(second_id, verification["request_id"])

    assert utils.get_json(f"{url}/review").status_code == 404
    assert utils.post_json(f"{url}/approve", {}).status_code == 404
    assert utils.post_json(f"{url}/reject", {}).status_code == 404
    assert _verification_request(app, db, verification["request_id"])[0] == "inbox"


def test_verification_get_review_shows_profile_and_members(
    client, app, db, seeder, utils, verification
):
    seeder.create_admin_unit_member(
        verification["source_admin_unit_id"], ["event_verifier"], "member@test.de"
    )
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE adminunit SET description = 'Beschreibung',"
                " url = 'https://example.com', email = 'crew@example.com',"
                " phone = '0123', fax = '0124', logo_id = :image_id WHERE id = :id"
            ),
            {"id": verification["source_admin_unit_id"], "image_id": image_id},
        )
        db.session.commit()

    review = utils.get_json_ok(f"{verification['url']}/review").json

    assert review["id"] == verification["request_id"]
    assert review["review_status"] == "inbox"
    organization = review["organization"]
    assert organization["name"] == "Verein"
    assert organization["description"] == "Beschreibung"
    assert organization["url"] == "https://example.com"
    assert organization["email"] == "crew@example.com"
    assert organization["phone"] == "0123"
    assert organization["fax"] == "0124"
    assert organization["logo_url"].startswith("/image/")
    assert organization["is_verified"] is False
    assert {"email": "member@test.de", "roles": ["Veranstaltungsexpert:in"]} in review[
        "members"
    ]
    assert "Verein" in review["auto_verify_description"]
    assert [(c["value"], c["label"]) for c in review["rejection_reasons"]] == [
        (0, "Ohne Grund"),
        (1, "Nicht zuständig"),
        (2, "Fehlende Informationen"),
        (3, "Unbekannt"),
        (4, "Unseriös"),
        (5, "Unzulässig"),
        (6, "Nicht relevant"),
    ]
    assert review["list_url"] == (
        f"/manage/admin_unit/{verification['admin_unit_id']}/incoming_organization_verification_requests"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("incoming_verification_requests_postal_codes", ["99999"]),
        ("incoming_verification_requests_allowed", False),
    ],
)
def test_verification_approve_ignores_creation_only_rules(
    client, app, db, utils, verification, field, value
):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        setattr(db.session.get(AdminUnit, verification["admin_unit_id"]), field, value)
        db.session.commit()

    response = utils.post_json(f"{verification['url']}/approve", {"auto_verify": False})

    assert response.status_code == 200
    assert _verification_request(app, db, verification["request_id"])[0] == "verified"
    relation = _relation(
        app, verification["admin_unit_id"], verification["source_admin_unit_id"]
    )
    assert relation is not None
    assert relation["verify"]


def test_verification_approve(client, app, db, utils, verification):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, verification["source_admin_unit_id"]).description = (
            "Beschreibung"
        )
        db.session.commit()

    response = utils.post_json(f"{verification['url']}/approve", {"auto_verify": True})

    assert response.status_code == 200
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{verification['admin_unit_id']}/incoming_organization_verification_requests"
    )
    assert _flashes(client) == [("success", "Organisation erfolgreich verifiziert")]

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "mitglied@verein.de"
    assert _verification_request(app, db, verification["request_id"])[0] == "verified"

    relation = _relation(
        app, verification["admin_unit_id"], verification["source_admin_unit_id"]
    )
    assert relation is not None
    assert relation["verify"]
    assert relation["auto_verify"]


def test_verification_approve_without_auto_verify(client, app, db, utils, verification):
    response = utils.post_json(f"{verification['url']}/approve", {})

    assert response.status_code == 200
    relation = _relation(
        app, verification["admin_unit_id"], verification["source_admin_unit_id"]
    )
    assert relation["verify"]
    assert not relation["auto_verify"]


def test_verification_approve_with_verifier_widget_colors(
    client, app, db, utils, verification
):
    with app.app_context():
        from colour import Color

        from project.infrastructure.models import AdminUnit

        verifier = db.session.get(AdminUnit, verification["admin_unit_id"])
        verifier.widget_background_color = Color("#eceef0")
        verifier.widget_primary_color = Color("#b09641")
        verifier.widget_link_color = Color("#7b2424")
        db.session.commit()

    response = utils.post_json(f"{verification['url']}/approve", {"auto_verify": True})

    assert response.status_code == 200
    assert _verification_request(app, db, verification["request_id"])[0] == "verified"


def test_verification_approve_db_error(client, mocker, utils, verification):
    utils.mock_db_commit(mocker)

    response = utils.post_json(f"{verification['url']}/approve", {})

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_verification_approve_twice_is_400(client, utils, verification):
    assert utils.post_json(f"{verification['url']}/approve", {}).status_code == 200

    response = utils.post_json(f"{verification['url']}/approve", {})

    assert response.status_code == 400
    assert response.json["message"]


def test_verification_reject_without_reason(client, app, db, utils, verification):
    response = utils.post_json(f"{verification['url']}/reject", {"rejection_reason": 0})

    assert response.status_code == 200
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{verification['admin_unit_id']}/incoming_organization_verification_requests"
    )
    assert _flashes(client) == [
        ("success", "Verifizierungsanfrage erfolgreich aktualisiert")
    ]
    assert _verification_request(app, db, verification["request_id"]) == (
        "rejected",
        None,
    )


def test_verification_reject_with_reason(client, app, db, utils, verification):
    response = utils.post_json(f"{verification['url']}/reject", {"rejection_reason": 6})

    assert response.status_code == 200
    status, reason = _verification_request(app, db, verification["request_id"])
    assert status == "rejected"
    assert reason.name == "irrelevant"


def test_verification_reject_with_unknown_reason_is_422(
    client, app, db, utils, verification
):
    response = utils.post_json(
        f"{verification['url']}/reject", {"rejection_reason": 99}
    )

    assert response.status_code == 422
    assert _verification_request(app, db, verification["request_id"])[0] == "inbox"
