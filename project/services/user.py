from flask_security import hash_password

from project import user_datastore
from project.models import Role, User


def create_user(email, password):
    return user_datastore.create_user(email=email, password=hash_password(password))


def add_roles_to_user(email, roles):
    user = find_user_by_email(email)

    if user is None:
        raise ValueError("User with given email does not exist.")

    for role in roles:
        user_datastore.add_role_to_user(user, role)


def add_admin_roles_to_user(email):
    add_roles_to_user(email, ["admin", "event_verifier", "early_adopter"])


def remove_roles_from_user(email, roles):
    user = find_user_by_email(email)

    for role in roles:
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
    role.remove_permissions(role.get_permissions())
    role.add_permissions(permissions)
    return role


def find_user_by_email(email):
    return user_datastore.find_user(email=email, case_insensitive=True)


def get_user(id):
    return user_datastore.find_user(id=id)


def find_all_users_with_role(role_name: str) -> list:
    return User.query.filter(User.roles.any(Role.name == role_name)).all()
