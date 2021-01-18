import click
from flask.cli import AppGroup
from project import app, dump_path
from project.models import (
    Event,
    EventPlace,
    EventReference,
    Location,
    EventCategory,
    EventOrganizer,
    Image,
    AdminUnit,
)
from sqlalchemy.orm import joinedload
import json
from project.api.event.schemas import EventDumpSchema
from project.api.place.schemas import PlaceDumpSchema
from project.api.location.schemas import LocationDumpSchema
from project.api.event_category.schemas import EventCategoryDumpSchema
from project.api.organizer.schemas import OrganizerDumpSchema
from project.api.image.schemas import ImageDumpSchema
from project.api.organization.schemas import OrganizationDumpSchema
from project.api.event_reference.schemas import EventReferenceDumpSchema
import os
import shutil
import pathlib

dump_cli = AppGroup("dump")


def dump_items(items, schema, file_base_name, dump_path):
    result = schema.dump(items)
    path = os.path.join(dump_path, file_base_name + ".json")

    with open(path, "w") as outfile:
        json.dump(result, outfile, ensure_ascii=False)

    click.echo(f"{len(items)} item(s) dumped to {path}.")


@dump_cli.command("all")
def dump_all():
    # Setup temp dir
    tmp_path = os.path.join(dump_path, "tmp")

    try:
        original_umask = os.umask(0)
        pathlib.Path(tmp_path).mkdir(parents=True, exist_ok=True)
    finally:
        os.umask(original_umask)

    # Events
    events = Event.query.options(joinedload(Event.categories)).all()
    dump_items(events, EventDumpSchema(many=True), "events", tmp_path)

    # Places
    places = EventPlace.query.all()
    dump_items(places, PlaceDumpSchema(many=True), "places", tmp_path)

    # Locations
    locations = Location.query.all()
    dump_items(locations, LocationDumpSchema(many=True), "locations", tmp_path)

    # Event categories
    event_categories = EventCategory.query.all()
    dump_items(
        event_categories,
        EventCategoryDumpSchema(many=True),
        "event_categories",
        tmp_path,
    )

    # Organizers
    organizers = EventOrganizer.query.all()
    dump_items(organizers, OrganizerDumpSchema(many=True), "organizers", tmp_path)

    # Images
    images = Image.query.all()
    dump_items(images, ImageDumpSchema(many=True), "images", tmp_path)

    # Organizations
    organizations = AdminUnit.query.all()
    dump_items(
        organizations, OrganizationDumpSchema(many=True), "organizations", tmp_path
    )

    # Event references
    event_references = EventReference.query.all()
    dump_items(
        event_references,
        EventReferenceDumpSchema(many=True),
        "event_references",
        tmp_path,
    )

    # Zip
    zip_base_name = os.path.join(dump_path, "all")
    zip_path = shutil.make_archive(zip_base_name, "zip", tmp_path)
    click.echo(f"Zipped all up to {zip_path}.")

    # Clean up temp dir
    shutil.rmtree(tmp_path, ignore_errors=True)


app.cli.add_command(dump_cli)
