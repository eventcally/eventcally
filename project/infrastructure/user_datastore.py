"""Flask-Security datastore access: the one place that talks to the user datastore
(users, roles, ToS). It deliberately imports no `project.infrastructure.models`."""

import datetime

from flask import current_app
from flask_security import hash_password

from project.infrastructure.extensions import db


def create_user(email, password):
    return current_app.extensions["security"].datastore.create_user(
        email=email, password=hash_password(password)
    )


def add_roles_to_user(email, roles):
    user = find_user_by_email(email)

    if user is None:
        raise ValueError("User with given email does not exist.")

    for role in roles:
        current_app.extensions["security"].datastore.add_role_to_user(user, role)


def add_admin_roles_to_user(email):
    add_roles_to_user(email, ["admin"])


def remove_roles_from_user(email, roles):
    user = find_user_by_email(email)

    for role in roles:  # pragma: no cover
        current_app.extensions["security"].datastore.remove_role_from_user(user, role)


def remove_all_roles_from_user(email):
    user = find_user_by_email(email)
    remove_roles_from_user(email, user.roles)


def set_roles_for_user(email, roles):
    remove_all_roles_from_user(email)
    add_roles_to_user(email, roles)


def find_user_by_email(email):
    return current_app.extensions["security"].datastore.find_user(
        email=email, case_insensitive=True
    )


def get_user(id):
    return current_app.extensions["security"].datastore.find_user(id=id)


def delete_user(user):
    current_app.extensions["security"].datastore.delete_user(user)
    db.session.commit()


def set_user_accepted_tos(user):
    user.tos_accepted_at = datetime.datetime.now(datetime.UTC)
