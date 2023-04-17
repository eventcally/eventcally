from enum import IntEnum

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
)
from sqlalchemy.orm import declared_attr, relationship

from project.dbtypes import IntegerEnum
from project.models.functions import create_tsvector


class EventTargetGroupOrigin(IntEnum):
    both = 1
    tourist = 2
    resident = 3


class EventAttendanceMode(IntEnum):
    offline = 1
    online = 2
    mixed = 3


class EventMixin(object):
    name = Column(Unicode(255), nullable=False)
    external_link = Column(String(255))
    description = Column(UnicodeText(), nullable=True)

    ticket_link = Column(String(255))
    tags = Column(UnicodeText())
    kid_friendly = Column(Boolean())
    accessible_for_free = Column(Boolean())
    age_from = Column(Integer())
    age_to = Column(Integer())
    target_group_origin = Column(IntegerEnum(EventTargetGroupOrigin))
    attendance_mode = Column(IntegerEnum(EventAttendanceMode))
    registration_required = Column(Boolean())
    booked_up = Column(Boolean())
    expected_participants = Column(Integer())
    price_info = Column(UnicodeText())

    @declared_attr
    def __ts_vector__(cls):
        return create_tsvector((cls.name, "A"), (cls.tags, "B"), (cls.description, "C"))

    @declared_attr
    def photo_id(cls):
        return Column("photo_id", ForeignKey("image.id"))

    @declared_attr
    def photo(cls):
        return relationship(
            "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
        )

    def purge_event_mixin(self):
        if self.photo and self.photo.is_empty():
            self.photo_id = None
