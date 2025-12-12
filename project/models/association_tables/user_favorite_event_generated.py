from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class UserFavoriteEventGeneratedMixin:
    __tablename__ = "user_favoriteevents"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
