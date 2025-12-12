from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class RolesUsersGeneratedMixin:
    __tablename__ = "roles_users"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role_id = db.Column(
        db.Integer, db.ForeignKey("role.id", ondelete="CASCADE"), nullable=False
    )
