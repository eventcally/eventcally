from sqlalchemy import Column, Integer, String, Unicode
from sqlalchemy.orm import deferred

from project import db
from project.dateutils import gmt_tz
from project.models.trackable_mixin import TrackableMixin


class Image(db.Model, TrackableMixin):
    __tablename__ = "image"
    id = Column(Integer(), primary_key=True)
    data = deferred(db.Column(db.LargeBinary))
    encoding_format = Column(String(80))
    copyright_text = Column(Unicode(255))

    def is_empty(self):
        return not self.data

    def get_hash(self):
        return (
            int(self.updated_at.replace(tzinfo=gmt_tz).timestamp() * 1000)
            if self.updated_at
            else 0
        )
