import click
from flask.cli import AppGroup

from project import app, db
from project.services.user import add_admin_roles_to_user

user_cli = AppGroup("user")


@user_cli.command("add-admin-roles")
@click.argument("email")
def add_admin_roles(email):
    add_admin_roles_to_user(email)
    db.session.commit()
    click.echo(f"Admin roles were added to {email}.")


app.cli.add_command(user_cli)
