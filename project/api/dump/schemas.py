from project.api import marshmallow
from marshmallow import fields
from project.api.event.schemas import EventDumpSchema
from project.api.place.schemas import PlaceDumpSchema
from project.api.location.schemas import LocationDumpSchema
from project.api.event_category.schemas import EventCategoryDumpSchema
from project.api.organizer.schemas import OrganizerDumpSchema
from project.api.image.schemas import ImageDumpSchema
from project.api.organization.schemas import OrganizationDumpSchema
from project.api.event_reference.schemas import EventReferenceDumpSchema


class DumpResponseSchema(marshmallow.Schema):
    events = fields.List(fields.Nested(EventDumpSchema))
    places = fields.List(fields.Nested(PlaceDumpSchema))
    locations = fields.List(fields.Nested(LocationDumpSchema))
    event_categories = fields.List(fields.Nested(EventCategoryDumpSchema))
    organizers = fields.List(fields.Nested(OrganizerDumpSchema))
    images = fields.List(fields.Nested(ImageDumpSchema))
    organizations = fields.List(fields.Nested(OrganizationDumpSchema))
    event_references = fields.List(fields.Nested(EventReferenceDumpSchema))
