import datetime

from flask_security import hash_password

from project import db, user_datastore
from project.models import Event, Role, User, UserFavoriteEvents
from project.models.admin_unit import AdminUnitMember


def create_user(email, password):
    return user_datastore.create_user(email=email, password=hash_password(password))


def add_roles_to_user(email, roles):
    user = find_user_by_email(email)

    if user is None:
        raise ValueError("User with given email does not exist.")

    for role in roles:
        user_datastore.add_role_to_user(user, role)


def add_admin_roles_to_user(email):
    add_roles_to_user(email, ["admin"])


def remove_roles_from_user(email, roles):
    user = find_user_by_email(email)

    for role in roles:  # pragma: no cover
        user_datastore.remove_role_from_user(user, role)


def remove_all_roles_from_user(email):
    user = find_user_by_email(email)
    remove_roles_from_user(email, user.roles)


def set_roles_for_user(email, roles):
    remove_all_roles_from_user(email)
    add_roles_to_user(email, roles)


def upsert_user_role(role_name, role_title, permissions):
    role = user_datastore.find_or_create_role(role_name)
    role.title = role_title
    role.permissions = permissions
    return role


def find_user_by_email(email):
    return user_datastore.find_user(email=email, case_insensitive=True)


def get_user(id):
    return user_datastore.find_user(id=id)


def find_all_users_with_role(role_name: str) -> list:
    return User.query.filter(User.roles.any(Role.name == role_name)).all()


def get_favorite_events_query(user_id: int):
    return Event.query.join(
        UserFavoriteEvents, UserFavoriteEvents.event_id == Event.id
    ).filter(UserFavoriteEvents.user_id == user_id)


def get_favorite_event(user_id: int, event_id: int) -> UserFavoriteEvents:
    return UserFavoriteEvents.query.filter(
        UserFavoriteEvents.event_id == event_id,
        UserFavoriteEvents.user_id == user_id,
    ).first()


def has_favorite_event(user_id: int, event_id: int) -> bool:
    if get_favorite_event(user_id, event_id):
        return True

    return False


def add_favorite_event(user_id: int, event_id: int) -> bool:
    from project import db

    if has_favorite_event(user_id, event_id):
        return False

    favorite = UserFavoriteEvents(user_id=user_id, event_id=event_id)
    db.session.add(favorite)
    return True


def remove_favorite_event(user_id: int, event_id: int):
    from project import db

    favorite = get_favorite_event(user_id, event_id)

    if not favorite:
        return False

    db.session.delete(favorite)
    return True


def get_users_with_due_delete_request():
    due = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=3)
    return User.query.filter(User.deletion_requested_at < due).all()


def get_ghost_users():
    created_before = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=31)
    return (
        User.query.filter(User.created_at < created_before)
        .filter(User.confirmed_at.is_(None))
        .all()
    )


def delete_user(user):
    user_datastore.delete_user(user)
    db.session.commit()


def is_user_admin_member(user: User) -> bool:
    return (
        AdminUnitMember.query.filter(
            AdminUnitMember.user_id == user.id,
            AdminUnitMember.is_admin,
        ).first()
        is not None
    )


def set_user_accepted_tos(user: User):
    user.tos_accepted_at = datetime.datetime.now(datetime.UTC)
