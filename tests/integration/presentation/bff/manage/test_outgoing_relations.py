import pytest

BASE_URL = "/bff/manage/organizations/{}/outgoing-organization-relations"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(
        f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_relation/create"
    )


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _urls(admin_unit_id, relation_id=0):
    base = BASE_URL.format(admin_unit_id)
    return dict(
        create_form=f"{base}/create-form",
        form=f"{base}/{relation_id}",
        lookup=f"{base}/organizations",
        base=base,
    )


def _relation(app, relation_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        return relation and dict(
            verify=relation.verify,
            auto=relation.auto_verify_event_reference_requests,
        )


def _find_relation(app, source_id, target_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = AdminUnitRelation.query.filter(
            AdminUnitRelation.source_admin_unit_id == source_id,
            AdminUnitRelation.target_admin_unit_id == target_id,
        ).first()
        return relation and relation.id


def _allow_verify_other(app, db, admin_unit_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = True
        db.session.commit()


@pytest.fixture
def setup(client, app, db, seeder, utils):
    """The organization may verify others; `other` is a verified second one."""
    _, admin_unit_id = seeder.setup_base()
    _allow_verify_other(app, db, admin_unit_id)
    other_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Other Crew", verified=True
    )
    _shell(utils, admin_unit_id)
    return admin_unit_id, other_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    urls = _urls(admin_unit_id, 1)

    for call in (
        lambda: utils.get_json(urls["create_form"]),
        lambda: utils.get_json(urls["form"]),
        lambda: utils.get_json(urls["lookup"]),
        lambda: utils.post_json(urls["base"], dict(target_admin_unit_id=1)),
        lambda: utils.put_json(urls["form"], dict()),
    ):
        assert call().status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")
    urls = _urls(admin_unit_id, 1)

    assert utils.get_json(urls["create_form"]).status_code == 403
    assert utils.get_json(urls["form"]).status_code == 403
    assert utils.get_json(urls["lookup"]).status_code == 403
    assert (
        utils.post_json(urls["base"], dict(target_admin_unit_id=1)).status_code == 403
    )
    assert utils.put_json(urls["form"], dict()).status_code == 403


def test_relation_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(other_id, admin_unit_id)
    urls = _urls(admin_unit_id, relation_id)

    assert utils.get_json(urls["form"]).status_code == 404
    assert utils.put_json(urls["form"], dict(verify=True)).status_code == 404
    assert _relation(app, relation_id)["verify"] is False


def test_unknown_relation_is_404(client, utils, setup):
    admin_unit_id, _ = setup

    assert utils.get_json(_urls(admin_unit_id, 4711)["form"]).status_code == 404


def test_foreign_organization_is_403(client, seeder, utils, setup):
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="third@test.de"), name="Andere Crew"
    )
    urls = _urls(other_id, 1)

    assert utils.get_json(urls["create_form"]).status_code == 403
    assert (
        utils.post_json(urls["base"], dict(target_admin_unit_id=1)).status_code == 403
    )


# create form


def test_get_create_form(client, utils, setup):
    admin_unit_id, _ = setup

    body = utils.get_json_ok(_urls(admin_unit_id)["create_form"]).json

    assert body["id"] is None
    assert body["target"] is None
    assert body["verify"] is False
    assert body["auto_verify_event_reference_requests"] is False
    assert body["can_verify_other"] is True
    assert body["list_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_relations"
    )


def test_get_create_form_prefill(client, utils, setup):
    admin_unit_id, other_id = setup

    body = utils.get_json_ok(
        _urls(admin_unit_id)["create_form"] + f"?target={other_id}&verify=1"
    ).json

    assert body["target"] == dict(id=other_id, name="Other Crew")
    assert body["verify"] is True


def test_get_create_form_ignores_unknown_target(client, utils, setup):
    admin_unit_id, _ = setup

    body = utils.get_json_ok(_urls(admin_unit_id)["create_form"] + "?target=4711").json

    assert body["target"] is None


def test_get_create_form_without_verify_permission(client, app, db, utils, setup):
    admin_unit_id, other_id = setup
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = False
        db.session.commit()

    body = utils.get_json_ok(
        _urls(admin_unit_id)["create_form"] + f"?target={other_id}&verify=1"
    ).json

    assert body["can_verify_other"] is False
    assert body["verify"] is False


# update form


def test_get_form(client, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(
        admin_unit_id, other_id, auto_verify_event_reference_requests=True, verify=True
    )

    body = utils.get_json_ok(_urls(admin_unit_id, relation_id)["form"]).json

    assert body["id"] == relation_id
    assert body["target"] == dict(id=other_id, name="Other Crew")
    assert body["verify"] is True
    assert body["auto_verify_event_reference_requests"] is True
    assert body["can_verify_other"] is True


# lookup


def test_lookup_includes_unverified_with_permission(client, seeder, utils, setup):
    admin_unit_id, other_id = setup
    unverified_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Other Unverified"
    )
    urls = _urls(admin_unit_id)

    items = utils.get_json_ok(urls["lookup"] + "?keyword=Other").json["items"]

    assert {item["id"] for item in items} == {other_id, unverified_id}


def test_lookup_hides_unverified_without_permission(
    client, app, db, seeder, utils, setup
):
    admin_unit_id, other_id = setup
    seeder.create_admin_unit(seeder.create_user("third@test.de"), "Other Unverified")
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = False
        db.session.commit()

    items = utils.get_json_ok(_urls(admin_unit_id)["lookup"] + "?keyword=Other").json[
        "items"
    ]

    assert items == [dict(id=other_id, name="Other Crew")]


# create


def test_create(client, app, utils, setup):
    admin_unit_id, other_id = setup

    response = utils.post_json(
        _urls(admin_unit_id)["base"],
        dict(
            target_admin_unit_id=other_id,
            verify=True,
            auto_verify_event_reference_requests=True,
        ),
    )

    assert response.status_code == 201
    relation_id = _find_relation(app, admin_unit_id, other_id)
    assert response.json == dict(
        id=relation_id,
        redirect_url=f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_relations",
    )
    assert _relation(app, relation_id) == dict(verify=True, auto=True)
    assert _flashes(client) == [
        ("success", "Ausgehende Organisationsbeziehung erfolgreich erstellt")
    ]


def test_create_ignores_verify_without_permission(client, app, db, utils, setup):
    admin_unit_id, other_id = setup
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = False
        db.session.commit()

    response = utils.post_json(
        _urls(admin_unit_id)["base"],
        dict(target_admin_unit_id=other_id, verify=True),
    )

    assert response.status_code == 201
    relation_id = _find_relation(app, admin_unit_id, other_id)
    assert _relation(app, relation_id) == dict(verify=False, auto=False)


def test_create_requires_target(client, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id)["base"], dict())

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["target_admin_unit_id"]
    assert response.json["errors"][0]["msg"] == "Dieses Feld ist erforderlich."


def test_create_duplicate_is_a_field_error(client, app, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(admin_unit_id, other_id)

    response = utils.post_json(
        _urls(admin_unit_id)["base"], dict(target_admin_unit_id=other_id, verify=True)
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["target_admin_unit_id"]
    assert response.json["errors"][0]["msg"] == (
        "Es besteht bereits eine Beziehung zu dieser Organisation."
    )
    assert _relation(app, relation_id)["verify"] is False


def test_create_requires_csrf(client, seeder):
    _, admin_unit_id = seeder.setup_base()

    response = client.post(
        _urls(admin_unit_id)["base"], json=dict(target_admin_unit_id=1)
    )

    assert response.status_code == 400


# update


def test_update(client, app, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(admin_unit_id, other_id)

    response = utils.put_json(
        _urls(admin_unit_id, relation_id)["form"],
        dict(verify=True, auto_verify_event_reference_requests=True),
    )

    assert response.status_code == 200
    assert response.json == dict(
        id=relation_id,
        redirect_url=f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_relations",
    )
    assert _relation(app, relation_id) == dict(verify=True, auto=True)
    assert _flashes(client) == [
        ("success", "Ausgehende Organisationsbeziehung erfolgreich aktualisiert")
    ]


def test_update_keeps_verify_without_permission(client, app, db, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(
        admin_unit_id, other_id, verify=True
    )
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = False
        db.session.commit()

    response = utils.put_json(
        _urls(admin_unit_id, relation_id)["form"],
        dict(verify=False, auto_verify_event_reference_requests=True),
    )

    assert response.status_code == 200
    assert _relation(app, relation_id) == dict(verify=True, auto=True)


# list


def _stamp(app, db, target_id, updated_at):
    from sqlalchemy import text

    with app.app_context():
        db.session.execute(
            text("UPDATE adminunit SET updated_at = :u WHERE id = :id"),
            {"u": updated_at, "id": target_id},
        )
        db.session.commit()


@pytest.fixture
def listed(client, app, db, seeder, utils, setup):
    """Relations to `Alpha` (verify) and `beta` (auto verify), `Alpha` modified first."""
    admin_unit_id, other_id = setup
    alpha_id = seeder.create_admin_unit(seeder.create_user("a@test.de"), "Alpha Crew")
    beta_id = seeder.create_admin_unit(seeder.create_user("b@test.de"), "beta Crew")
    alpha_relation = seeder.create_admin_unit_relation(
        admin_unit_id, alpha_id, verify=True
    )
    beta_relation = seeder.create_admin_unit_relation(
        admin_unit_id, beta_id, auto_verify_event_reference_requests=True
    )
    _stamp(app, db, alpha_id, "2026-01-01")
    _stamp(app, db, beta_id, "2026-03-01")
    return admin_unit_id, alpha_id, beta_id, alpha_relation, beta_relation


def _names(response):
    return [item["organization_name"] for item in response.json["items"]]


def test_list(client, utils, listed):
    admin_unit_id, alpha_id, _, alpha_relation, _ = listed

    response = utils.get_json_ok(_urls(admin_unit_id)["base"])

    assert _names(response) == ["Alpha Crew", "beta Crew"]
    assert response.json["can_write"] is True
    assert response.json["can_verify_other"] is True
    assert response.json["per_page"] == 50
    first = response.json["items"][0]
    assert first["id"] == alpha_relation
    assert first["organization_id"] == alpha_id
    assert first["verify"] is True
    assert first["auto_verify_event_reference_requests"] is False
    assert first["last_modified_at"] is not None


def test_list_sort_search_and_filters(client, utils, listed):
    admin_unit_id = listed[0]
    base = _urls(admin_unit_id)["base"]

    assert _names(utils.get_json_ok(base + "?sort=-last_modified_at")) == [
        "beta Crew",
        "Alpha Crew",
    ]
    assert _names(utils.get_json_ok(base + "?keyword=BE")) == ["beta Crew"]
    assert _names(utils.get_json_ok(base + "?verify=1")) == ["Alpha Crew"]
    assert _names(utils.get_json_ok(base + "?verify=0")) == ["beta Crew"]
    assert _names(
        utils.get_json_ok(base + "?auto_verify_event_reference_requests=1")
    ) == ["beta Crew"]


def test_list_ignores_the_verify_filter_without_permission(
    client, app, db, utils, listed
):
    admin_unit_id = listed[0]
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = False
        db.session.commit()

    response = utils.get_json_ok(_urls(admin_unit_id)["base"] + "?verify=1")

    assert response.json["can_verify_other"] is False
    assert _names(response) == ["Alpha Crew", "beta Crew"]


def test_list_out_of_range_is_404(client, utils, listed):
    assert utils.get_json(_urls(listed[0])["base"] + "?page=9").status_code == 404


def test_list_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")

    assert utils.get_json(_urls(admin_unit_id)["base"]).status_code == 403


# delete


def test_delete(client, app, utils, listed):
    admin_unit_id, _, _, alpha_relation, _ = listed

    response = utils.post_json(
        _urls(admin_unit_id, alpha_relation)["form"] + "/delete", dict()
    )

    assert response.status_code == 200
    assert response.json == dict(
        message="Ausgehende Organisationsbeziehung erfolgreich gelöscht"
    )
    assert _relation(app, alpha_relation) is None


def test_delete_without_permission_is_403(client, app, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    target_id = seeder.create_admin_unit(seeder.create_user("t@test.de"), "Target")
    relation_id = seeder.create_admin_unit_relation(admin_unit_id, target_id)
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")

    response = utils.post_json(
        _urls(admin_unit_id, relation_id)["form"] + "/delete", dict()
    )

    assert response.status_code == 403
    assert _relation(app, relation_id) is not None


def test_delete_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, other_id = setup
    relation_id = seeder.create_admin_unit_relation(other_id, admin_unit_id)

    response = utils.post_json(
        _urls(admin_unit_id, relation_id)["form"] + "/delete", dict()
    )

    assert response.status_code == 404
    assert _relation(app, relation_id) is not None


def test_delete_with_db_error_is_400(client, app, mocker, utils, listed):
    admin_unit_id, _, _, alpha_relation, _ = listed
    utils.mock_db_commit(mocker)

    response = utils.post_json(
        _urls(admin_unit_id, alpha_relation)["form"] + "/delete", dict()
    )

    assert response.status_code == 400
