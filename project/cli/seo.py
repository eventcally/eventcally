import os
import shutil
from io import StringIO

import click
import requests
from flask import url_for
from flask.cli import AppGroup, with_appcontext
from sqlalchemy.orm import load_only

from project import app, cache_path, robots_txt_path, sitemap_path
from project.dateutils import get_today
from project.models import Event, EventDate
from project.utils import make_dir

seo_cli = AppGroup("seo")


@seo_cli.command("generate-sitemap")
@click.option("--pinggoogle/--no-pinggoogle", default=False)
@with_appcontext
def generate_sitemap(pinggoogle):
    click.echo("Generating sitemap..")
    make_dir(cache_path)

    buf = StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>')
    buf.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    today = get_today()
    events = (
        Event.query.options(load_only(Event.id, Event.updated_at))
        .filter(Event.dates.any(EventDate.start >= today))
        .all()
    )
    click.echo(f"Found {len(events)} events")

    for event in events:
        loc = url_for("event", event_id=event.id)
        lastmod = event.updated_at.strftime("%Y-%m-%d") if event.updated_at else None
        lastmod_tag = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        buf.write(f"<url><loc>{loc}</loc>{lastmod_tag}</url>")

    buf.write("</urlset>")

    with open(sitemap_path, "w") as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)

    size = os.path.getsize(sitemap_path)
    click.echo(f"Generated sitemap at {sitemap_path} ({size} Bytes)")

    if size > 52428800:  # pragma: no cover
        app.logger.error(f"Size of sitemap ({size} Bytes) is larger than 50MB.")

    if pinggoogle:  # pragma: no cover
        sitemap_url = requests.utils.quote(url_for("sitemap_xml"))
        google_url = f"http://www.google.com/ping?sitemap={sitemap_url}"
        click.echo(f"Pinging {google_url} ..")

        response = requests.get(google_url)
        click.echo(f"Response {response.status_code}")

        if response.status_code != 200:
            app.logger.error(
                f"Google ping returned unexpected status code {response.status_code}."
            )


@seo_cli.command("generate-robots-txt")
@with_appcontext
def generate_robots_txt():
    click.echo("Generating robots.txt..")
    make_dir(cache_path)

    buf = StringIO()
    buf.write(f"user-agent: *{os.linesep}")
    buf.write(f"Disallow: /{os.linesep}")
    buf.write(f"Allow: /eventdates{os.linesep}")
    buf.write(f"Allow: /eventdate/{os.linesep}")
    buf.write(f"Allow: /event/{os.linesep}")

    if os.path.exists(sitemap_path):
        sitemap_url = url_for("sitemap_xml")
        buf.write(f"Sitemap: {sitemap_url}{os.linesep}")

    with open(robots_txt_path, "w") as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)

    click.echo(f"Generated robots.txt at {robots_txt_path}")


app.cli.add_command(seo_cli)
