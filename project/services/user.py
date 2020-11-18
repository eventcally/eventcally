from project import user_datastore
from flask_security import hash_password


def upsert_user(email, password="password"):
    result = user_datastore.find_user(email=email)
    if result is None:
        result = user_datastore.create_user(
            email=email, password=hash_password(password)
        )
    return result


def add_roles_to_user(user_name, role_names):
    user = upsert_user(user_name)
    for role_name in role_names:
        user_datastore.add_role_to_user(user, role_name)


def add_admin_roles_to_user(user_name):
    add_roles_to_user(user_name, ["admin", "event_verifier"])


def upsert_user_role(role_name, role_title, permissions):
    role = user_datastore.find_or_create_role(role_name)
    role.title = role_title
    role.remove_permissions(role.get_permissions())
    role.add_permissions(permissions)
    return role


def find_user_by_email(email):
    return user_datastore.find_user(email=email)


def get_user(id):
    return user_datastore.get_user(id)
