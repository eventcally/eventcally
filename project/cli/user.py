import click
from flask.cli import AppGroup
from flask_security.confirmable import confirm_user

from project import app, db
from project.services.user import (
    add_admin_roles_to_user,
    create_user,
    find_user_by_email,
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
def create(email, password, confirm):
    user = create_user(email, password)

    if confirm:
        confirm_user(user)

    db.session.commit()
    click.echo(f"Created user {email}.")


@user_cli.command("confirm")
@click.argument("email")
def confirm(email):
    user = find_user_by_email(email)
    confirm_user(user)
    db.session.commit()
    click.echo(f"Confirmed user {email}.")


app.cli.add_command(user_cli)
