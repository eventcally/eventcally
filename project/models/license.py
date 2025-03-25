from sqlalchemy import Column, Integer, Unicode

from project import db
from project.models.trackable_mixin import TrackableMixin


class License(db.Model, TrackableMixin):
    __tablename__ = "license"
    id = Column(Integer(), primary_key=True)
    sort = Column(Integer(), nullable=False, default=0, server_default="0")
    code = Column(Unicode(255), unique=True)
    name = Column(Unicode(255), unique=True)
    url = Column(Unicode(255), unique=True)

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()
