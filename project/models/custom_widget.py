from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.dialects.postgresql import JSONB

from project import db
from project.models.trackable_mixin import TrackableMixin


class CustomWidget(db.Model, TrackableMixin):
    __tablename__ = "customwidget"
    id = Column(Integer(), primary_key=True)
    widget_type = Column(Unicode(255), nullable=False)
    name = Column(Unicode(255), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    settings = Column(JSONB)
