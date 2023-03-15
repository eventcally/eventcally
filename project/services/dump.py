import json
import os
import shutil

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from project import app, dump_path
from project.api.event.schemas import EventDumpSchema
from project.api.event_category.schemas import EventCategoryDumpSchema
from project.api.event_reference.schemas import EventReferenceDumpSchema
from project.api.organization.schemas import OrganizationDumpSchema
from project.api.organizer.schemas import OrganizerDumpSchema
from project.api.place.schemas import PlaceDumpSchema
from project.models import (
    AdminUnit,
    Event,
    EventCategory,
    EventOrganizer,
    EventPlace,
    EventReference,
    PublicStatus,
)
from project.utils import make_dir


def dump_items(items, schema, file_base_name, dump_path):
    result = schema.dump(items)
    path = os.path.join(dump_path, file_base_name + ".json")

    with open(path, "w") as outfile:
        json.dump(result, outfile, ensure_ascii=False)

    app.logger.info(f"{len(items)} item(s) dumped to {path}.")


def dump_all():
    # Setup temp dir
    tmp_path = os.path.join(dump_path, "tmp")
    make_dir(tmp_path)

    # Events
    events = (
        Event.query.join(Event.admin_unit)
        .options(joinedload(Event.categories))
        .filter(
            and_(
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )
        )
        .all()
    )
    dump_items(events, EventDumpSchema(many=True), "events", tmp_path)

    # Places
    places = EventPlace.query.all()
    dump_items(places, PlaceDumpSchema(many=True), "places", tmp_path)

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
    app.logger.info(f"Zipped all up to {zip_path}.")

    # Clean up temp dir
    shutil.rmtree(tmp_path, ignore_errors=True)
