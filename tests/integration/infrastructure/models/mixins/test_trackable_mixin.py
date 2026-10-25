import datetime


def _event(**kwargs):
    from project.infrastructure.models import Event

    return Event(**kwargs)


def test_last_modified_at_prefers_updated_at(app):
    created = datetime.datetime(2030, 1, 1)
    updated = datetime.datetime(2030, 2, 1)

    assert _event(created_at=created).last_modified_at == created
    assert _event(created_at=created, updated_at=updated).last_modified_at == updated


def test_labels_name_the_creating_and_updating_actor(app):
    from project.infrastructure.models import AppInstallation, OAuth2Client, User

    client = OAuth2Client()
    client.set_client_metadata({"client_name": "My App"})
    installation = AppInstallation(oauth2_client=client)
    by_user = _event(created_by=User(email="user@test.de"))
    by_app = _event(created_by_app_installation=installation)
    updated_by_user = _event(updated_by=User(email="editor@test.de"))
    updated_by_app = _event(updated_by_app_installation=installation)

    assert by_user.created_by_label == "user@test.de"
    assert by_app.created_by_label == "My App"
    assert updated_by_user.updated_by_label == "editor@test.de"
    assert updated_by_app.updated_by_label == "My App"


def test_get_hash_is_the_last_modification_in_milliseconds(app):
    updated = datetime.datetime(2030, 2, 1, 12, 0, 0)

    assert _event().get_hash() == 0
    assert _event(updated_at=updated).get_hash() == int(
        updated.replace(tzinfo=datetime.UTC).timestamp() * 1000
    )
