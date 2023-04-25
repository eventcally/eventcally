from sqlalchemy import event
from sqlalchemy.orm import Session

from project.models import IOwned


@event.listens_for(Session, "before_flush")
def before_flush(session, flush_context, instances):
    for instance in session.dirty:
        if isinstance(instance, IOwned):
            instance.before_flush(session, True)

    for instance in session.new:
        if isinstance(instance, IOwned):
            instance.before_flush(session, False)
