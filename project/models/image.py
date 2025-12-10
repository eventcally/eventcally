from sqlalchemy.event import listens_for

from project import db
from project.models.image_generated import ImageGeneratedMixin
from project.models.iowned import IOwned
from project.utils import make_check_violation


class Image(db.Model, ImageGeneratedMixin, IOwned):
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
