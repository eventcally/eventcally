from sqlalchemy import Column, Integer, UnicodeText

from project import db
from project.models.trackable_mixin import TrackableMixin


class Settings(db.Model, TrackableMixin):
    __tablename__ = "settings"
    id = Column(Integer(), primary_key=True)
    tos = Column(UnicodeText())
    legal_notice = Column(UnicodeText())
    contact = Column(UnicodeText())
    privacy = Column(UnicodeText())
    start_page = Column(UnicodeText())
