from marshmallow import fields

from project.presentation.api import marshmallow
from project.presentation.api.event.schemas import EventDumpSchema
from project.presentation.api.event_category.schemas import EventCategoryDumpSchema
from project.presentation.api.event_reference.schemas import EventReferenceDumpSchema
from project.presentation.api.image.schemas import ImageDumpSchema
from project.presentation.api.location.schemas import LocationDumpSchema
from project.presentation.api.organization.schemas import OrganizationDumpSchema
from project.presentation.api.organizer.schemas import OrganizerDumpSchema
from project.presentation.api.place.schemas import PlaceDumpSchema


class DumpResponseSchema(marshmallow.Schema):
    events = fields.List(fields.Nested(EventDumpSchema))
    places = fields.List(fields.Nested(PlaceDumpSchema))
    locations = fields.List(fields.Nested(LocationDumpSchema))
    event_categories = fields.List(fields.Nested(EventCategoryDumpSchema))
    organizers = fields.List(fields.Nested(OrganizerDumpSchema))
    images = fields.List(fields.Nested(ImageDumpSchema))
    organizations = fields.List(fields.Nested(OrganizationDumpSchema))
    event_references = fields.List(fields.Nested(EventReferenceDumpSchema))
