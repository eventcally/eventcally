import click
from flask.cli import AppGroup

from project import app
from project.cli import click_logging
from project.services import seo

seo_cli = AppGroup("seo")


@seo_cli.command("generate-sitemap")
@click.option("--pinggoogle/--no-pinggoogle", default=False)
@click_logging
def generate_sitemap(pinggoogle):
    seo.generate_sitemap(pinggoogle)


@seo_cli.command("generate-robots-txt")
@click_logging
def generate_robots_txt():
    seo.generate_robots_txt()


app.cli.add_command(seo_cli)
