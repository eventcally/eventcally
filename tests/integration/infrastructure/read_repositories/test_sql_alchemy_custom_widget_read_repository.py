"""SqlAlchemyCustomWidgetReadRepository against the database."""

from project.application.queries import ListCustomWidgetsQuery


def test_organization_exists_list_and_get(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    beta_id = seeder.insert_event_custom_widget(admin_unit_id, name="beta Widget")
    alpha_id = seeder.insert_event_custom_widget(
        admin_unit_id, widget_type="calendar", name="Alpha Widget"
    )

    with app.app_context():
        repo = app.container.read_repos.custom_widget_read_repo()

        with app.container.infrastructure.read_session_scope():
            exists = repo.organization_exists(admin_unit_id)
            missing_organization = repo.organization_exists(4711)
            everything = repo.list(ListCustomWidgetsQuery(admin_unit_id=admin_unit_id))
            filtered = repo.list(
                ListCustomWidgetsQuery(admin_unit_id=admin_unit_id, name="PHA")
            )
            widget = repo.get(beta_id)
            missing_widget = repo.get(4711)

    assert exists is True
    assert missing_organization is False
    assert [item.id for item in everything.items] == [alpha_id, beta_id]
    assert [item.id for item in filtered.items] == [alpha_id]
    assert widget.name == "beta Widget"
    assert widget.widget_type == "search"
    assert widget.settings == {"color": "black"}
    assert widget.admin_unit.id == admin_unit_id
    assert missing_widget is None
