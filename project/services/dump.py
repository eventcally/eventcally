import json
import os
import shutil

from flask import current_app

from project.application.queries import (
    GetImageFileQuery,
    ListDumpEventCategoriesQuery,
    ListDumpEventReferencesQuery,
    ListDumpEventsQuery,
    ListDumpOrganizationsQuery,
    ListDumpOrganizersQuery,
    ListDumpPlacesQuery,
)
from project.presentation.api.event.schemas import EventDumpSchema
from project.presentation.api.event_category.schemas import EventCategoryDumpSchema
from project.presentation.api.event_reference.schemas import EventReferenceDumpSchema
from project.presentation.api.organization.schemas import OrganizationDumpSchema
from project.presentation.api.organizer.schemas import OrganizerDumpSchema
from project.presentation.api.place.schemas import PlaceDumpSchema
from project.shared.imageutils import get_image_from_bytes
from project.shared.paths import dump_org_path, dump_path
from project.shared.utils import clear_files_in_dir, make_dir

BATCH_SIZE = 200


def _query_bus():
    return current_app.container.cqrs.query_bus()


def _collect(make_query) -> list:
    """Every item of a keyset-paged query: `make_query(after_id)` per batch."""
    items = list()
    after_id = 0

    while True:
        batch = _query_bus().handle(make_query(after_id))
        items.extend(batch)

        if len(batch) < BATCH_SIZE:
            return items

        after_id = batch[-1].id


class Dumper(object):
    def __init__(self, dump_base_path, file_base_name):
        self.dump_base_path = dump_base_path
        self.file_base_name = file_base_name
        self.tmp_path = None

    def dump(self):
        self.setup_tmp_dir()
        self.dump_data()
        self.zip_tmp_dir()
        self.clean_up_tmp_dir()

    def dump_data(self):
        # Events
        events = _collect(
            lambda after_id: ListDumpEventsQuery(
                public_only=True, after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(events, EventDumpSchema(many=True), "events")

        # Places
        places = _collect(
            lambda after_id: ListDumpPlacesQuery(after_id=after_id, limit=BATCH_SIZE)
        )
        self.dump_items(places, PlaceDumpSchema(many=True), "places")

        # Event categories
        event_categories = _query_bus().handle(ListDumpEventCategoriesQuery())
        self.dump_items(
            event_categories,
            EventCategoryDumpSchema(many=True),
            "event_categories",
        )

        # Organizers
        organizers = _collect(
            lambda after_id: ListDumpOrganizersQuery(
                after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(organizers, OrganizerDumpSchema(many=True), "organizers")

        # Organizations
        organizations = _collect(
            lambda after_id: ListDumpOrganizationsQuery(
                after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(
            organizations, OrganizationDumpSchema(many=True), "organizations"
        )

        # Event references
        event_references = _collect(
            lambda after_id: ListDumpEventReferencesQuery(
                after_id=after_id, limit=BATCH_SIZE
            )
        )
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

        current_app.logger.info(f"{len(items)} item(s) dumped to {path}.")

    def dump_item(self, items, schema, file_base_name):
        result = schema.dump(items)
        path = os.path.join(self.tmp_path, file_base_name + ".json")

        with open(path, "w") as outfile:
            json.dump(result, outfile, ensure_ascii=False, indent=4)

        current_app.logger.info(f"Item dumped to {path}.")

    def setup_tmp_dir(self):
        self.tmp_path = os.path.join(self.dump_base_path, f"tmp-{self.file_base_name}")
        make_dir(self.tmp_path)

    def clean_up_tmp_dir(self):
        shutil.rmtree(self.tmp_path, ignore_errors=True)

    def zip_tmp_dir(self):
        zip_base_name = os.path.join(self.dump_base_path, self.file_base_name)
        zip_path = shutil.make_archive(zip_base_name, "zip", self.tmp_path)
        current_app.logger.info(f"Zipped all up to {zip_path}.")

    def dump_image(self, image):
        if not image:
            return

        image_file = _query_bus().handle(GetImageFileQuery(id=image.id))
        extension = image_file.get_file_extension()
        file_path = os.path.join(self.tmp_path, f"{image.id}.{extension}")
        get_image_from_bytes(image_file.data).save(file_path)


class AdminUnitDumper(Dumper):
    def __init__(self, dump_base_path, admin_unit_id):
        super().__init__(dump_base_path, f"org-{admin_unit_id}")
        self.admin_unit_id = admin_unit_id

    def dump_data(self):
        admin_unit_id = self.admin_unit_id

        # Events
        events = _collect(
            lambda after_id: ListDumpEventsQuery(
                admin_unit_id=admin_unit_id, after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(events, EventDumpSchema(many=True), "events")
        for event in events:
            self.dump_image(event.photo)

        # Places
        places = _collect(
            lambda after_id: ListDumpPlacesQuery(
                admin_unit_id=admin_unit_id, after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(places, PlaceDumpSchema(many=True), "places")
        for place in places:
            self.dump_image(place.photo)

        # Event categories
        event_categories = _query_bus().handle(ListDumpEventCategoriesQuery())
        self.dump_items(
            event_categories,
            EventCategoryDumpSchema(many=True),
            "event_categories",
        )

        # Organizers
        organizers = _collect(
            lambda after_id: ListDumpOrganizersQuery(
                admin_unit_id=admin_unit_id, after_id=after_id, limit=BATCH_SIZE
            )
        )
        self.dump_items(organizers, OrganizerDumpSchema(many=True), "organizers")
        for organizer in organizers:
            self.dump_image(organizer.logo)

        # Organizations
        (organization,) = _query_bus().handle(
            ListDumpOrganizationsQuery(admin_unit_id=admin_unit_id)
        )
        self.dump_item(organization, OrganizationDumpSchema(), "organization")
        self.dump_image(organization.logo)


def dump_all():
    dumper = Dumper(dump_path, "all")
    dumper.dump()


def dump_admin_unit(admin_unit_id):
    dumper = AdminUnitDumper(dump_org_path, admin_unit_id)
    dumper.dump()


def clear_admin_unit_dumps():
    current_app.logger.info("Clearing admin unit dumps..")
    clear_files_in_dir(dump_org_path)
    current_app.logger.info("Done.")
