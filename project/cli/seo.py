from flask.cli import AppGroup

from project.cli import click_logging
from project.services import seo

seo_cli = AppGroup("seo")


@seo_cli.command("generate-sitemap")
@click_logging
def generate_sitemap():
    seo.generate_sitemap()


@seo_cli.command("generate-robots-txt")
@click_logging
def generate_robots_txt():
    seo.generate_robots_txt()
