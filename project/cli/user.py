import json

import click
from flask.cli import AppGroup
from flask_security.confirmable import confirm_user

from project import app, db
from project.services.user import (
    add_admin_roles_to_user,
    create_user,
    find_user_by_email,
    set_user_accepted_tos,
)

user_cli = AppGroup("user")


@user_cli.command("add-admin-roles")
@click.argument("email")
def add_admin_roles(email):
    add_admin_roles_to_user(email)
    db.session.commit()
    click.echo(f"Admin roles were added to {email}.")


@user_cli.command("create")
@click.argument("email")
@click.argument("password")
@click.option("--confirm/--no-confirm", default=False)
@click.option("--admin/--no-admin", default=False)
@click.option("--accept-tos/--no-accept-tos", default=False)
def create(email, password, confirm, admin, accept_tos):
    user = create_user(email, password)

    if confirm:
        confirm_user(user)

    if admin:
        add_admin_roles_to_user(email)

    if accept_tos:
        set_user_accepted_tos(user)

    db.session.commit()
    result = {"user_id": user.id}
    click.echo(json.dumps(result))


@user_cli.command("confirm")
@click.argument("email")
def confirm(email):
    user = find_user_by_email(email)
    confirm_user(user)
    db.session.commit()
    click.echo(f"Confirmed user {email}.")


app.cli.add_command(user_cli)
