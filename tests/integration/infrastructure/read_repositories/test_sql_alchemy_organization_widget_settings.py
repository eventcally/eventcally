"""The widget settings read of SqlAlchemyOrganizationReadRepository."""


def _read(app, object_id):
    with app.app_context():
        repo = app.container.read_repos.organization_read_repo()

        with app.container.infrastructure.read_session_scope():
            return repo.get_widget_settings(object_id)


def test_unconfigured_widget_has_no_styles(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    settings = _read(app, admin_unit_id)

    assert settings.id == admin_unit_id
    assert settings.widget_font is None
    assert settings.widget_primary_color is None


def test_configured_colors_come_as_hex_like_the_color_object(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.widget_font = "Arial"
        admin_unit.widget_background_color = "#123456"
        admin_unit.widget_primary_color = "#654321"
        admin_unit.widget_link_color = "#13579b"
        db.session.commit()

    settings = _read(app, admin_unit_id)

    assert settings.widget_font == "Arial"
    assert settings.widget_background_color == "#123456"
    assert settings.widget_primary_color == "#654321"
    assert settings.widget_link_color == "#13579b"


def test_unknown_organization_is_none(app, db):
    assert _read(app, 4711) is None


def test_verifiers_serving_a_postal_code(app, db, seeder):
    from project.application.queries import ListVerifierOrganizationsQuery, PageRequest

    _, verifier_id = seeder.setup_base(log_in=False, name="Verifier Crew")
    _, requester_id = seeder.setup_base(
        email="requester@test.de", name="Requester Crew", log_in=False
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        verifier = db.session.get(AdminUnit, verifier_id)
        verifier.can_verify_other = True
        verifier.incoming_verification_requests_allowed = True
        verifier.incoming_verification_requests_text = "Write us"
        db.session.commit()

    def verifiers(postal_code):
        with app.app_context():
            repo = app.container.read_repos.organization_read_repo()

            with app.container.infrastructure.read_session_scope():
                return repo.list_verifiers(
                    ListVerifierOrganizationsQuery(
                        postal_code=postal_code, page=PageRequest()
                    )
                )

    page = verifiers("12345")

    assert [o.name for o in page.items] == ["Verifier Crew"]
    assert page.items[0].incoming_verification_requests_text == "Write us"
    assert page.items[0].location.postalCode == "12345"
    assert page.total == 1

    with app.app_context():
        db.session.get(
            AdminUnit, verifier_id
        ).incoming_verification_requests_postal_codes = ["99999"]
        db.session.commit()

    assert verifiers("12345").items == []
    assert [o.name for o in verifiers("99999").items] == ["Verifier Crew"]
