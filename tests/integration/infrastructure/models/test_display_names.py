"""``__str__`` of the models Flask-Admin shows in its lists and selects."""


def test_user_and_member_labels(app):
    from project.infrastructure.models import AdminUnitMember, User

    user = User(email="user@test.de")

    assert str(user) == "user@test.de"
    assert str(AdminUnitMember(user=user)) == "user@test.de"


def test_event_place_and_client_labels(app):
    from project.infrastructure.models import EventPlace, OAuth2Client

    assert str(EventPlace(name="Town Hall")) == "Town Hall"

    client = OAuth2Client()
    client.set_client_metadata({"client_name": "My App"})
    assert str(client) == "My App"
