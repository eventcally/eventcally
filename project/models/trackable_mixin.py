import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, declared_attr, deferred, relationship

from project.dateutils import gmt_tz
from project.models.functions import _current_user_id_or_none


class TrackableMixin(object):
    @declared_attr
    def created_at(cls):
        return deferred(
            Column(DateTime, default=datetime.datetime.utcnow), group="trackable"
        )

    @declared_attr
    def updated_at(cls):
        return deferred(
            Column(
                DateTime,
                onupdate=datetime.datetime.utcnow,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by_id(cls):
        return deferred(
            Column(
                "created_by_id",
                ForeignKey("user.id", ondelete="SET NULL"),
                default=_current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.created_by_id" % cls.__name__,
            remote_side="User.id",
            backref=backref("created_%s" % cls.__tablename__, lazy=True),
        )

    @declared_attr
    def updated_by_id(cls):
        return deferred(
            Column(
                "updated_by_id",
                ForeignKey("user.id", ondelete="SET NULL"),
                onupdate=_current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.updated_by_id" % cls.__name__,
            remote_side="User.id",
            backref=backref("updated_%s" % cls.__tablename__, lazy=True),
        )

    @hybrid_property
    def last_modified_at(self):
        return self.updated_at if self.updated_at else self.created_at

    def get_hash(self):
        return (
            int(self.last_modified_at.replace(tzinfo=gmt_tz).timestamp() * 1000)
            if self.last_modified_at
            else 0
        )
