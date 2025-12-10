from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from project.dateutils import gmt_tz
from project.models.trackable_mixin_generated import TrackableGeneratedMixin


class TrackableMixin(TrackableGeneratedMixin):
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
