import datetime

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, declared_attr, deferred, relationship

from project.actor import current_actor
from project.dateutils import gmt_tz


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
                default=current_actor.current_user_id_or_none,
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
                onupdate=current_actor.current_user_id_or_none,
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

    @declared_attr
    def created_by_app_installation_id(cls):
        return deferred(
            Column(
                "created_by_app_installation_id",
                ForeignKey("app_installation.id", ondelete="SET NULL"),
                default=current_actor.current_app_installation_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by_app_installation(cls):
        return relationship(
            "AppInstallation",
            primaryjoin="AppInstallation.id == %s.created_by_app_installation_id"
            % cls.__name__,
            remote_side="AppInstallation.id",
            backref=backref("created_%s" % cls.__tablename__, lazy=True),
        )

    @declared_attr
    def updated_by_app_installation_id(cls):
        return deferred(
            Column(
                "updated_by_app_installation_id",
                ForeignKey("app_installation.id", ondelete="SET NULL"),
                onupdate=current_actor.current_app_installation_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by_app_installation(cls):
        return relationship(
            "AppInstallation",
            primaryjoin="AppInstallation.id == %s.updated_by_app_installation_id"
            % cls.__name__,
            remote_side="AppInstallation.id",
            backref=backref("updated_%s" % cls.__tablename__, lazy=True),
        )

    @hybrid_property
    def last_modified_at(self):
        return self.updated_at if self.updated_at else self.created_at

    @last_modified_at.expression
    def last_modified_at(cls):
        return func.coalesce(cls.updated_at, cls.created_at)

    @property
    def created_by_label(self):
        if self.created_by:
            return self.created_by.email

        if self.created_by_app_installation:
            return self.created_by_app_installation.oauth2_client.client_name

        return None  # pragma: no cover

    @property
    def updated_by_label(self):
        if self.updated_by:
            return self.updated_by.email

        if self.updated_by_app_installation:
            return self.updated_by_app_installation.oauth2_client.client_name

        return None  # pragma: no cover

    def get_hash(self):
        return (
            int(self.last_modified_at.replace(tzinfo=gmt_tz).timestamp() * 1000)
            if self.last_modified_at
            else 0
        )
