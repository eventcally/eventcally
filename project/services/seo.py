import logging
import os
import shutil
from io import StringIO

from flask import current_app, url_for

from project.application.queries import ListSitemapEventsQuery
from project.shared.paths import cache_path, robots_txt_path, sitemap_path
from project.shared.utils import make_dir

logger = logging.getLogger(__name__)


def generate_sitemap():
    logger.info("Generating sitemap")
    make_dir(cache_path)

    buf = StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>')
    buf.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    events = current_app.container.cqrs.query_bus().handle(ListSitemapEventsQuery())
    logger.info("Found sitemap events", extra={"count": len(events)})

    for event in events:
        loc = url_for("main.event", event_id=event.id)
        lastmod = (
            event.last_modified_at.strftime("%Y-%m-%d")
            if event.last_modified_at
            else None
        )
        lastmod_tag = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        buf.write(f"<url><loc>{loc}</loc>{lastmod_tag}</url>")

    buf.write("</urlset>")

    with open(sitemap_path, "w") as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)

    size = os.path.getsize(sitemap_path)
    logger.info("Generated sitemap", extra={"path": sitemap_path, "size_bytes": size})

    if size > 52428800:  # pragma: no cover
        logger.error("Sitemap is larger than 50MB", extra={"size_bytes": size})


def generate_robots_txt():
    logger.info("Generating robots.txt")
    make_dir(cache_path)

    buf = StringIO()
    buf.write(f"user-agent: *{os.linesep}")
    buf.write(f"Disallow: /{os.linesep}")
    buf.write(f"Allow: /eventdates{os.linesep}")
    buf.write(f"Allow: /eventdate/{os.linesep}")
    buf.write(f"Allow: /event/{os.linesep}")

    if os.path.exists(sitemap_path):
        sitemap_url = url_for("main.sitemap_xml")
        buf.write(f"Sitemap: {sitemap_url}{os.linesep}")

    with open(robots_txt_path, "w") as fd:
        buf.seek(0)
        shutil.copyfileobj(buf, fd)

    logger.info("Generated robots.txt", extra={"path": robots_txt_path})
