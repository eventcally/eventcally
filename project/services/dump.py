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
from project.imageutils import get_image_from_bytes
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


class Dumper(object):
    def __init__(self, dump_path, file_base_name):
        self.dump_path = dump_path
        self.file_base_name = file_base_name
        self.tmp_path = None

    def dump(self):
        self.setup_tmp_dir()
        self.dump_data()
        self.zip_tmp_dir()
        self.clean_up_tmp_dir()

    def dump_data(self):
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
        self.dump_items(events, EventDumpSchema(many=True), "events")

        # Places
        places = EventPlace.query.all()
        self.dump_items(places, PlaceDumpSchema(many=True), "places")

        # Event categories
        event_categories = EventCategory.query.all()
        self.dump_items(
            event_categories,
            EventCategoryDumpSchema(many=True),
            "event_categories",
        )

        # Organizers
        organizers = EventOrganizer.query.all()
        self.dump_items(organizers, OrganizerDumpSchema(many=True), "organizers")

        # Organizations
        organizations = AdminUnit.query.all()
        self.dump_items(
            organizations, OrganizationDumpSchema(many=True), "organizations"
        )

        # Event references
        event_references = EventReference.query.all()
        self.dump_items(
            event_references,
            EventReferenceDumpSchema(many=True),
            "event_references",
        )

    def dump_items(self, items, schema, file_base_name):
        result = schema.dump(items)
        path = os.path.join(self.tmp_path, file_base_name + ".json")

        with open(path, "w") as outfile:
            json.dump(result, outfile, ensure_ascii=False, indent=4)

        app.logger.info(f"{len(items)} item(s) dumped to {path}.")

    def dump_item(self, items, schema, file_base_name):  # pragma: no cover
        result = schema.dump(items)
        path = os.path.join(self.tmp_path, file_base_name + ".json")

        with open(path, "w") as outfile:
            json.dump(result, outfile, ensure_ascii=False, indent=4)

        app.logger.info(f"Item dumped to {path}.")

    def setup_tmp_dir(self):
        self.tmp_path = os.path.join(self.dump_path, f"tmp-{self.file_base_name}")
        make_dir(self.tmp_path)

    def clean_up_tmp_dir(self):
        shutil.rmtree(self.tmp_path, ignore_errors=True)

    def zip_tmp_dir(self):
        zip_base_name = os.path.join(dump_path, self.file_base_name)
        zip_path = shutil.make_archive(zip_base_name, "zip", self.tmp_path)
        app.logger.info(f"Zipped all up to {zip_path}.")

    def dump_image(self, image):  # pragma: no cover
        if not image:
            return

        extension = image.get_file_extension()
        file_path = os.path.join(self.tmp_path, f"{image.id}.{extension}")
        get_image_from_bytes(image.data).save(file_path)


class AdminUnitDumper(Dumper):  # pragma: no cover
    def __init__(self, dump_path, admin_unit_id):
        super().__init__(dump_path, f"org-{admin_unit_id}")
        self.admin_unit_id = admin_unit_id

    def dump_data(self):
        # Events
        events = (
            Event.query.join(Event.admin_unit)
            .options(joinedload(Event.categories))
            .filter(Event.admin_unit_id == self.admin_unit_id)
            .all()
        )
        self.dump_items(events, EventDumpSchema(many=True), "events")
        for event in events:
            self.dump_image(event.photo)

        # Places
        places = EventPlace.query.filter(
            EventPlace.admin_unit_id == self.admin_unit_id
        ).all()
        self.dump_items(places, PlaceDumpSchema(many=True), "places")
        for place in places:
            self.dump_image(place.photo)

        # Event categories
        event_categories = EventCategory.query.all()
        self.dump_items(
            event_categories,
            EventCategoryDumpSchema(many=True),
            "event_categories",
        )

        # Organizers
        organizers = EventOrganizer.query.filter(
            EventOrganizer.admin_unit_id == self.admin_unit_id
        ).all()
        self.dump_items(organizers, OrganizerDumpSchema(many=True), "organizers")
        for organizer in organizers:
            self.dump_image(organizer.logo)

        # Organizations
        organization = AdminUnit.query.get(self.admin_unit_id)
        self.dump_item(organization, OrganizationDumpSchema(), "organization")
        self.dump_image(organization.logo)


def dump_all():
    dumper = Dumper(dump_path, "all")
    dumper.dump()


def dump_admin_unit(admin_unit_id):  # pragma: no cover
    dumper = AdminUnitDumper(dump_path, admin_unit_id)
    dumper.dump()
