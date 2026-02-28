from __future__ import annotations

from typing import Optional

from sqlalchemy.event import listens_for

from project import db
from project.domain import events
from project.domain.commands import CreateImage, UpdateImage
from project.domain.events import ImageUpdated
from project.domain.events.image_created import ImageCreated
from project.domain.types import Unsetable, unset
from project.models.image_generated import ImageGeneratedMixin
from project.models.iowned import IOwned
from project.utils import make_check_violation


class Image(db.Model, ImageGeneratedMixin, IOwned):

    @classmethod
    def create(
        cls,
        cmd: Optional[CreateImage],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd is None:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance = cls()
        instance.data = cmd.data
        instance.encoding_format = cmd.encoding_format
        instance.copyright_text = cmd.copyright_text
        instance.license_id = cmd.license_id
        instance.validate()
        setattr(parent, field_name, instance)

        event = ImageCreated(
            encoding_format=instance.encoding_format,
            copyright_text=instance.copyright_text,
            license_id=instance.license_id,
        )
        setattr(parent_event, event_field_name, event)

    @classmethod
    def update(
        cls,
        cmd: Unsetable[UpdateImage],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd == unset:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance = getattr(parent, field_name)

        if cmd is None:
            if instance is not None:
                setattr(parent, field_name, None)
                setattr(parent_event, event_field_name, None)
            return

        if instance is None:
            instance = cls()

        event = ImageUpdated()
        if instance._update_field(cmd, None, "data"):
            event.data_changed = True
        instance._update_field(cmd, event, "encoding_format")
        instance._update_field(cmd, event, "copyright_text")
        instance._update_field(cmd, event, "license_id")
        instance.validate()

        setattr(parent, field_name, instance)

        if event.has_changed_values():
            setattr(parent_event, event_field_name, event)

    def is_empty(self):
        return not self.data

    def get_file_extension(self):
        return self.encoding_format.split("/")[-1] if self.encoding_format else "png"

    def before_flush(self, session, is_dirty):
        if self.is_empty():
            if self.admin_unit:
                self.admin_unit.logo = None

            if self.event:
                self.event.photo = None

            if self.event_organizer:
                self.event_organizer.logo = None

            if self.event_place:
                self.event_place.photo = None

            if is_dirty:
                session.delete(self)

    def validate(self):
        if (
            not self.copyright_text or not self.copyright_text.strip()
        ) and not self.is_empty():
            raise make_check_violation("Copyright text is required.")


@listens_for(Image, "before_insert")
@listens_for(Image, "before_update")
def before_saving_image(mapper, connect, self):
    self.validate()
