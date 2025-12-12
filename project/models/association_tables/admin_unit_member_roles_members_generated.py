from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class AdminUnitMemberRolesMembersGeneratedMixin:
    __tablename__ = "adminunitmemberroles_members"
    __table_args__ = (UniqueConstraint("member_id", "role_id"),)
    id = Column(Integer(), primary_key=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey("adminunitmember.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("adminunitmemberrole.id", ondelete="CASCADE"),
        nullable=False,
    )
