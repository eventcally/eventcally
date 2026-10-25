import pytest

from project.infrastructure import user_datastore


def test_add_roles_to_unknown_user_raises(app, db):
    with app.app_context():
        with pytest.raises(ValueError, match="does not exist"):
            user_datastore.add_roles_to_user("nobody@test.de", ["admin"])


def test_create_find_and_delete_user(app, db):
    with app.app_context():
        user = user_datastore.create_user("Datastore@test.de", "password")
        db.session.commit()
        user_id = user.id

        assert user_datastore.find_user_by_email("datastore@TEST.de").id == user_id
        assert user_datastore.get_user(user_id).email == "Datastore@test.de"

        user_datastore.delete_user(user)

        assert user_datastore.get_user(user_id) is None
