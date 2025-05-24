from dateutil.relativedelta import relativedelta
from sqlalchemy import Boolean, Column, Integer, UnicodeText, func
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.models.functions import sanitize_allday_instance
from project.utils import make_check_violation


class EventDate(db.Model):
    __tablename__ = "eventdate"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    end = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )

    @hybrid_property
    def end_or_start(self):  # pragma: no cover
        return self.end if self.end else self.start

    @end_or_start.expression
    def end_or_start(cls):
        return func.coalesce(cls.end, cls.start)


@listens_for(EventDate, "before_insert")
@listens_for(EventDate, "before_update")
def purge_event_date(mapper, connect, self):
    sanitize_allday_instance(self)


class EventDateDefinition(db.Model):
    __tablename__ = "eventdatedefinition"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    recurrence_rule = Column(UnicodeText())

    def validate(self):
        if self.start and self.end:
            if self.start > self.end:
                raise make_check_violation("The start must be before the end.")

            max_end = self.start + relativedelta(days=180)
            if self.end > max_end:
                raise make_check_violation("An event can last a maximum of 180 days.")


@listens_for(EventDateDefinition, "before_insert")
@listens_for(EventDateDefinition, "before_update")
def before_saving_event_date_definition(mapper, connect, self):
    self.validate()
    sanitize_allday_instance(self)
