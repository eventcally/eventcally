from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.orm import deferred

from project import db
from project.models.trackable_mixin import TrackableMixin


class Settings(db.Model, TrackableMixin):
    __tablename__ = "settings"
    id = Column(Integer(), primary_key=True)
    tos = deferred(Column(UnicodeText()))
    legal_notice = deferred(Column(UnicodeText()))
    contact = deferred(Column(UnicodeText()))
    privacy = deferred(Column(UnicodeText()))
    start_page = deferred(Column(UnicodeText()))
    announcement = deferred(Column(UnicodeText()))
