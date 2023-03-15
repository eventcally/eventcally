import click
from flask.cli import AppGroup, with_appcontext

from project import app
from project.services import seo

seo_cli = AppGroup("seo")


@seo_cli.command("generate-sitemap")
@click.option("--pinggoogle/--no-pinggoogle", default=False)
@with_appcontext
def generate_sitemap(pinggoogle):
    seo.generate_sitemap(pinggoogle)


@seo_cli.command("generate-robots-txt")
@with_appcontext
def generate_robots_txt():
    seo.generate_robots_txt()


app.cli.add_command(seo_cli)
