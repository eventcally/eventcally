from sqlalchemy import Column, Integer, String, Unicode
from sqlalchemy.event import listens_for
from sqlalchemy.orm import deferred

from project import db
from project.models.iowned import IOwned
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class Image(db.Model, TrackableMixin, IOwned):
    __tablename__ = "image"
    id = Column(Integer(), primary_key=True)
    data = deferred(db.Column(db.LargeBinary))
    encoding_format = Column(String(80))
    copyright_text = Column(Unicode(255))

    adminunit = db.relationship("AdminUnit", uselist=False)
    event = db.relationship("Event", uselist=False)
    eventorganizer = db.relationship("EventOrganizer", uselist=False)
    eventplace = db.relationship("EventPlace", uselist=False)

    def is_empty(self):
        return not self.data

    def get_file_extension(self):
        return self.encoding_format.split("/")[-1] if self.encoding_format else "png"

    def before_flush(self, session, is_dirty):
        if self.is_empty():
            if self.adminunit:
                self.adminunit.logo = None

            if self.event:
                self.event.photo = None

            if self.eventorganizer:
                self.eventorganizer.logo = None

            if self.eventplace:
                self.eventplace.photo = None

            if is_dirty:
                session.delete(self)

    def validate(self):
        if (
            not self.copyright_text or not self.copyright_text.strip()
        ) and not self.is_empty():
            raise make_check_violation("Copyright text is required.")


@listens_for(Image, "before_insert")
@listens_for(Image, "before_update")
def before_saving_image(mapper, connect, self):
    self.validate()
