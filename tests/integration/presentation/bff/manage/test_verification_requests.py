import pytest
from sqlalchemy import text

BASE = "/bff/manage/organizations/{}"
INCOMING = BASE + "/incoming-verification-requests"
OUTGOING = BASE + "/outgoing-verification-requests"
VERIFIERS = BASE + "/verifier-organizations"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(
        f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_verification_requests"
    )


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _set(app, db, request_id, **values):
    columns = ", ".join(f"{key} = :{key}" for key in values)
    with app.app_context():
        db.session.execute(
            text(f"UPDATE adminunitverificationrequest SET {columns} WHERE id = :id"),
            dict(values, id=request_id),
        )
        db.session.commit()


def _request_ids(app, source_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest

        return [
            r.id
            for r in AdminUnitVerificationRequest.query.filter_by(
                source_admin_unit_id=source_id
            ).all()
        ]


@pytest.fixture
def unverified(client, seeder, utils):
    """The logged in organization is unverified; `Stadtmarketing` can verify it."""
    (
        _,
        verifier_id,
        _,
        admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()
    return admin_unit_id, verifier_id


# access


def test_anonymous_is_401(client, utils):
    for url in (
        INCOMING.format(1),
        OUTGOING.format(1),
        OUTGOING.format(1) + "/1",
        VERIFIERS.format(1),
    ):
        assert utils.get_json(url).status_code == 401

    assert utils.post_json(OUTGOING.format(1), dict(target_id=1)).status_code == 401
    assert (
        utils.post_json(OUTGOING.format(1) + "/1/withdraw", dict()).status_code == 401
    )


def test_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")

    for url in (
        INCOMING.format(admin_unit_id),
        OUTGOING.format(admin_unit_id),
        OUTGOING.format(admin_unit_id) + "/1",
        VERIFIERS.format(admin_unit_id),
    ):
        assert utils.get_json(url).status_code == 403

    assert (
        utils.post_json(OUTGOING.format(admin_unit_id), dict(target_id=1)).status_code
        == 403
    )
    assert (
        utils.post_json(
            OUTGOING.format(admin_unit_id) + "/1/withdraw", dict()
        ).status_code
        == 403
    )


# incoming list


@pytest.fixture
def incoming(app, db, seeder):
    """Two requests to the organization: an older rejected and a newer inbox one."""
    _, admin_unit_id = seeder.setup_base()
    alpha_id = seeder.create_admin_unit(
        seeder.create_user("alpha@test.de"), "Alpha Crew", verified=False
    )
    beta_id = seeder.create_admin_unit(
        seeder.create_user("beta@test.de"), "Beta Crew", verified=False
    )
    older = seeder.create_admin_unit_verification_request(alpha_id, admin_unit_id)
    newer = seeder.create_admin_unit_verification_request(beta_id, admin_unit_id)
    _set(app, db, older, created_at="2026-01-01", review_status=3)
    _set(app, db, newer, created_at="2026-02-01")
    return admin_unit_id, alpha_id, beta_id, older, newer


def test_incoming_list(utils, incoming):
    admin_unit_id, alpha_id, beta_id, older, newer = incoming

    response = utils.get_json_ok(INCOMING.format(admin_unit_id))

    assert response.json["can_write"] is True
    assert response.json["per_page"] == 50
    assert [i["id"] for i in response.json["items"]] == [newer, older]
    first, second = response.json["items"]
    assert first["organization_id"] == beta_id
    assert first["organization_name"] == "Beta Crew"
    assert first["review_status"] == 1
    assert first["review_status_label"] == "Ungeprüft"
    assert first["created_at"].startswith("2026-02-01")
    assert first["can_review"] is True
    assert second["review_status_label"] == "Abgelehnt"
    assert second["can_review"] is True
    assert response.json["review_status_choices"] == [
        {"value": -1, "label": "Alle"},
        {"value": 1, "label": "Ungeprüft"},
        {"value": 2, "label": "Verifiziert"},
        {"value": 3, "label": "Abgelehnt"},
    ]


def test_incoming_list_verified_cannot_be_reviewed(app, db, utils, incoming):
    admin_unit_id, _, _, older, newer = incoming
    _set(app, db, newer, review_status=2)

    items = utils.get_json_ok(INCOMING.format(admin_unit_id)).json["items"]

    assert [(i["id"], i["can_review"]) for i in items] == [
        (newer, False),
        (older, True),
    ]
    assert items[0]["review_status_label"] == "Verifiziert"


@pytest.mark.parametrize(
    "query,count",
    [
        ("", 2),
        ("?review_status=-1", 2),
        ("?review_status=3", 1),
        ("?review_status=x", 2),
    ],
)
def test_incoming_list_filter(utils, incoming, query, count):
    response = utils.get_json(INCOMING.format(incoming[0]) + query)

    # A status that is no integer is a validation error, the rest filters.
    if query.endswith("x"):
        assert response.status_code == 422
    else:
        assert len(response.json["items"]) == count


def test_incoming_list_unknown_status_is_no_filter(utils, incoming):
    response = utils.get_json_ok(INCOMING.format(incoming[0]) + "?review_status=9")

    assert len(response.json["items"]) == 2


def test_incoming_list_out_of_range_is_404(utils, incoming):
    assert utils.get_json(INCOMING.format(incoming[0]) + "?page=3").status_code == 404


# outgoing list


def test_outgoing_list_suggests_the_request_dialog(client, seeder, utils, unverified):
    admin_unit_id, verifier_id = unverified

    response = utils.get_json_ok(OUTGOING.format(admin_unit_id))

    assert response.json["items"] == []
    assert response.json["suggest_create"] is True
    assert response.json["can_write"] is True


def test_outgoing_list(app, db, seeder, utils, unverified):
    admin_unit_id, verifier_id = unverified
    request_id = seeder.create_admin_unit_verification_request(
        admin_unit_id, verifier_id
    )
    _set(app, db, request_id, created_at="2026-02-01", review_status=3)

    response = utils.get_json_ok(OUTGOING.format(admin_unit_id))

    assert response.json["suggest_create"] is False
    assert response.json["items"] == [
        dict(
            id=request_id,
            organization_id=verifier_id,
            organization_name="Stadtmarketing",
            review_status=3,
            review_status_label="Abgelehnt",
            created_at="2026-02-01T00:00:00",
            can_review=False,
        )
    ]


def test_outgoing_list_of_a_verified_organization_suggests_nothing(
    client, seeder, utils
):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_json_ok(OUTGOING.format(admin_unit_id))

    assert response.json["suggest_create"] is False


def test_outgoing_list_out_of_range_is_404(utils, unverified):
    assert utils.get_json(OUTGOING.format(unverified[0]) + "?page=2").status_code == 404


# outgoing read


@pytest.fixture
def requested(app, db, seeder, unverified):
    admin_unit_id, verifier_id = unverified
    request_id = seeder.create_admin_unit_verification_request(
        admin_unit_id, verifier_id
    )
    return admin_unit_id, verifier_id, request_id


def test_outgoing_read(app, db, utils, requested):
    admin_unit_id, verifier_id, request_id = requested
    _set(app, db, request_id, review_status=3, rejection_reason=3)

    body = utils.get_json_ok(OUTGOING.format(admin_unit_id) + f"/{request_id}").json

    assert body["id"] == request_id
    assert body["organization_id"] == verifier_id
    assert body["organization_name"] == "Stadtmarketing"
    assert body["review_status"] == 3
    assert body["review_status_label"] == "Abgelehnt"
    assert body["rejection_reason_label"] == "Unbekannt"
    assert body["can_write"] is True
    assert body["audit"] is not None


def test_outgoing_read_without_rejection_reason(utils, requested):
    admin_unit_id, _, request_id = requested

    body = utils.get_json_ok(OUTGOING.format(admin_unit_id) + f"/{request_id}").json

    assert body["review_status_label"] == "Ungeprüft"
    assert body["rejection_reason_label"] is None


def test_outgoing_read_of_another_organization_is_404(utils, seeder, requested):
    admin_unit_id, verifier_id, _ = requested
    other_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Dritte Crew", verified=False
    )
    foreign_id = seeder.create_admin_unit_verification_request(
        other_unit_id, verifier_id
    )

    _shell(utils, admin_unit_id)
    url = OUTGOING.format(admin_unit_id) + f"/{foreign_id}"

    assert utils.get_json(url).status_code == 404
    assert utils.post_json(url + "/withdraw", dict(inline=True)).status_code == 404


def test_outgoing_read_unknown_is_404(utils, unverified):
    assert utils.get_json(OUTGOING.format(unverified[0]) + "/4711").status_code == 404


# withdraw


def test_withdraw_flashes_for_the_list(client, app, utils, requested):
    admin_unit_id, _, request_id = requested
    _shell(utils, admin_unit_id)

    response = utils.post_json(
        OUTGOING.format(admin_unit_id) + f"/{request_id}/withdraw", dict()
    )

    assert response.status_code == 200
    assert response.json == dict(
        message="Verifizierungsanfrage erfolgreich gelöscht",
        redirect_url=f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_verification_requests",
    )
    assert _flashes(client) == [
        ("success", "Verifizierungsanfrage erfolgreich gelöscht")
    ]
    assert _request_ids(app, admin_unit_id) == []


def test_withdraw_inline_does_not_flash(client, app, utils, requested):
    admin_unit_id, _, request_id = requested
    _shell(utils, admin_unit_id)

    response = utils.post_json(
        OUTGOING.format(admin_unit_id) + f"/{request_id}/withdraw",
        dict(inline=True),
    )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert not session.get("_flashes")
    assert _request_ids(app, admin_unit_id) == []


def test_withdraw_with_db_error_is_400(client, app, mocker, utils, requested):
    admin_unit_id, _, request_id = requested
    _shell(utils, admin_unit_id)
    utils.mock_db_commit(mocker)

    response = utils.post_json(
        OUTGOING.format(admin_unit_id) + f"/{request_id}/withdraw", dict()
    )

    assert response.status_code == 400


# verifier organizations


def test_verifiers(client, seeder, utils, unverified):
    admin_unit_id, verifier_id = unverified

    body = utils.get_json_ok(VERIFIERS.format(admin_unit_id)).json

    assert body["organization_name"] == "Verein"
    assert body["postal_code"] == "12345"
    assert body["total"] == 1
    assert body["items"] == [
        dict(
            id=verifier_id,
            name="Stadtmarketing",
            is_verified=True,
            location=body["items"][0]["location"],
            logo_url=None,
            description=body["items"][0]["description"],
            incoming_verification_requests_text="Please give us a call",
            can_request=True,
        )
    ]


def test_verifiers_outside_the_allowed_postal_codes(app, db, utils, unverified):
    admin_unit_id, verifier_id = unverified
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(
            AdminUnit, verifier_id
        ).incoming_verification_requests_postal_codes = ["99999"]
        db.session.commit()

    body = utils.get_json_ok(VERIFIERS.format(admin_unit_id)).json

    assert body["items"] == []
    assert body["total"] == 0


def test_verifiers_out_of_range_is_404(utils, unverified):
    assert (
        utils.get_json(VERIFIERS.format(unverified[0]) + "?page=2").status_code == 404
    )


def test_verifiers_of_an_organization_without_postal_code(app, db, utils, unverified):
    admin_unit_id, _ = unverified
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).location.postalCode = None
        db.session.commit()

    body = utils.get_json_ok(VERIFIERS.format(admin_unit_id)).json

    assert body["postal_code"] is None


def test_verifiers_with_a_logo(app, db, seeder, utils, unverified):
    admin_unit_id, verifier_id = unverified
    image_id = seeder.upsert_default_image()
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, verifier_id).logo_id = image_id
        db.session.commit()

    body = utils.get_json_ok(VERIFIERS.format(admin_unit_id)).json

    assert body["items"][0]["logo_url"].startswith(f"/image/{image_id}")


# create


def test_create(client, app, utils, unverified):
    admin_unit_id, verifier_id = unverified
    _shell(utils, admin_unit_id)

    response = utils.post_json(
        OUTGOING.format(admin_unit_id), dict(target_id=verifier_id)
    )

    assert response.status_code == 201
    assert response.json["message"].startswith(
        "Verifizierungsanfrage erfolgreich erstellt."
    )

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "test@test.de"

    with app.app_context():
        from project.infrastructure.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        created = AdminUnitVerificationRequest.query.filter_by(
            source_admin_unit_id=admin_unit_id, target_admin_unit_id=verifier_id
        ).one()
        assert created.review_status == AdminUnitVerificationRequestReviewStatus.inbox


def test_create_outside_the_allowed_postal_codes_is_400(app, db, utils, unverified):
    admin_unit_id, verifier_id = unverified
    _shell(utils, admin_unit_id)
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(
            AdminUnit, verifier_id
        ).incoming_verification_requests_postal_codes = ["99999"]
        db.session.commit()

    response = utils.post_json(
        OUTGOING.format(admin_unit_id), dict(target_id=verifier_id)
    )

    assert response.status_code == 400
    assert response.json["message"] == (
        "Von dieser Organisation kann keine Verifizierung angefragt werden."
    )
    assert _request_ids(app, admin_unit_id) == []


def test_create_for_an_unknown_organization_is_404(utils, unverified):
    _shell(utils, unverified[0])

    response = utils.post_json(OUTGOING.format(unverified[0]), dict(target_id=4711))

    assert response.status_code == 404


def test_create_with_db_error_is_400(client, mocker, utils, unverified):
    admin_unit_id, verifier_id = unverified
    _shell(utils, admin_unit_id)
    utils.mock_db_commit(mocker)

    response = utils.post_json(
        OUTGOING.format(admin_unit_id), dict(target_id=verifier_id)
    )

    assert response.status_code == 400
