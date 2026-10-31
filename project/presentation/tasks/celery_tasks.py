import logging

from celery import group
from celery.schedules import crontab
from flask import current_app

from project.application.queries import (
    ListGhostUserIdsQuery,
    ListOldEventIdsQuery,
    ListOrganizationIdsDueForDeletionQuery,
    ListRecurringEventIdsQuery,
    ListUserIdsDueForDeletionQuery,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.celery_app import celery
from project.infrastructure.extensions import db

logger = logging.getLogger(__name__)


def _query_bus():
    return current_app.container.cqrs.query_bus()


def _message_bus():
    return current_app.container.cqrs.message_bus()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=0, minute=0), clear_images_task)
    sender.add_periodic_task(crontab(hour=0, minute=5), clear_admin_unit_dumps_task)
    sender.add_periodic_task(
        crontab(hour=0, minute=30), delete_admin_units_with_due_request_task
    )
    sender.add_periodic_task(
        crontab(hour=0, minute=40), delete_user_with_due_request_task
    )
    sender.add_periodic_task(crontab(hour=0, minute=45), delete_ghost_users_task)
    sender.add_periodic_task(crontab(hour=0, minute=50), delete_old_events_task)
    sender.add_periodic_task(crontab(hour=0, minute=55), delete_old_webhook_events_task)
    sender.add_periodic_task(crontab(hour=1, minute=0), update_recurring_dates_task)
    sender.add_periodic_task(crontab(hour=2, minute=0), dump_all_task)
    sender.add_periodic_task(crontab(hour=3, minute=0), seo_generate_sitemap_task)
    sender.add_periodic_task(crontab(hour=4, minute=0), generate_robots_txt_task)


# Task names are a wire contract with queued messages and the beat schedule;
# they keep their original module path even if this module moves.
@celery.task(
    name="project.celery_tasks.delete_old_webhook_events_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_old_webhook_events_task():
    from project.application import commands

    command = commands.DeleteOldWebhookEventsCommand(actor=Actor())
    message_bus = _message_bus()
    message_bus.handle(command)


@celery.task(
    name="project.celery_tasks.clear_images_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def clear_images_task():
    from project.services.cache import clear_images

    clear_images()


def update_recurring_dates():
    """Refreshes the dates of all recurring events, one command (one commit) per event
    so a broken event neither blocks nor rolls back the others."""
    from project.application import commands

    message_bus = _message_bus()
    event_ids = _query_bus().handle(ListRecurringEventIdsQuery())
    updated = 0

    for event_id in event_ids:
        try:
            message_bus.handle(
                commands.UpdateEventRecurringDatesCommand(
                    actor=Actor(), event_id=event_id
                )
            )
            updated += 1
        except Exception:
            logger.exception(
                "Failed to update the recurring dates of the event",
                extra={"event_id": event_id},
            )

    logger.info("Updated recurring dates", extra={"count": updated})


@celery.task(
    name="project.celery_tasks.update_recurring_dates_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def update_recurring_dates_task():
    try:
        update_recurring_dates()
    except Exception:
        logger.exception("Failed update_recurring_dates_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.dump_all_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_all_task():
    from project.services.dump import dump_all

    try:
        dump_all()
    except Exception:
        logger.exception("Failed dump_all_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.dump_admin_unit_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_admin_unit_task(admin_unit_id):
    from project.services.dump import dump_admin_unit

    try:
        dump_admin_unit(admin_unit_id)
    except Exception:
        logger.exception(
            "Failed dump_admin_unit_task", extra={"organization_id": admin_unit_id}
        )
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.clear_admin_unit_dumps_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def clear_admin_unit_dumps_task():
    from project.services.dump import clear_admin_unit_dumps

    clear_admin_unit_dumps()


@celery.task(
    name="project.celery_tasks.delete_admin_units_with_due_request_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_admin_units_with_due_request_task():
    try:
        admin_unit_ids = _query_bus().handle(ListOrganizationIdsDueForDeletionQuery())

        if not admin_unit_ids:
            return

        group(delete_admin_unit_task.s(id) for id in admin_unit_ids).delay()
    except Exception:
        logger.exception("Failed delete_admin_units_with_due_request_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_admin_unit_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_admin_unit_task(admin_unit_id):
    from project.application import commands

    try:
        deleted = _message_bus().handle(
            commands.DeleteOrganizationDueForDeletionCommand(
                actor=Actor(), organization_id=admin_unit_id
            )
        )

        if deleted:
            logger.info("Deleted admin unit", extra={"organization_id": admin_unit_id})
        else:
            logger.info("Skipped admin unit", extra={"organization_id": admin_unit_id})
    except Exception:
        logger.exception(
            "Failed to delete admin unit", extra={"organization_id": admin_unit_id}
        )
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_user_with_due_request_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_with_due_request_task():
    try:
        user_ids = _query_bus().handle(ListUserIdsDueForDeletionQuery())

        if not user_ids:
            return

        group(delete_user_task.s(id) for id in user_ids).delay()
    except Exception:
        logger.exception("Failed delete_user_with_due_request_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_ghost_users_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_ghost_users_task():
    try:
        user_ids = _query_bus().handle(ListGhostUserIdsQuery())

        if not user_ids:
            return

        group(delete_ghost_user_task.s(id) for id in user_ids).delay()
    except Exception:
        logger.exception("Failed delete_ghost_users_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_old_events_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_old_events_task():
    try:
        event_ids = _query_bus().handle(ListOldEventIdsQuery())

        if not event_ids:
            return

        group(delete_event_task.s(id) for id in event_ids).delay()
    except Exception:
        logger.exception("Failed delete_old_events_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_user_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_task(user_id):
    from project.application import commands

    try:
        deleted = _message_bus().handle(
            commands.DeleteUserDueForDeletionCommand(actor=Actor(), user_id=user_id)
        )

        if deleted:
            logger.info("Deleted user", extra={"user_id": user_id})
        else:
            logger.info("Skipped user", extra={"user_id": user_id})
    except Exception:
        logger.exception("Failed to delete user", extra={"user_id": user_id})
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_ghost_user_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_ghost_user_task(user_id):
    from project.application import commands

    try:
        deleted = _message_bus().handle(
            commands.DeleteGhostUserCommand(actor=Actor(), user_id=user_id)
        )

        if deleted:
            logger.info("Deleted ghost user", extra={"user_id": user_id})
        else:
            logger.info("Skipped ghost user", extra={"user_id": user_id})
    except Exception:
        logger.exception("Failed to delete ghost user", extra={"user_id": user_id})
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.delete_event_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_event_task(event_id):
    from project.application import commands

    try:
        deleted = _message_bus().handle(
            commands.DeleteOldEventCommand(actor=Actor(), event_id=event_id)
        )

        if deleted:
            logger.info("Deleted event", extra={"event_id": event_id})
        else:
            logger.info("Skipped event", extra={"event_id": event_id})
    except Exception:
        logger.exception("Failed to delete event", extra={"event_id": event_id})
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.seo_generate_sitemap_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def seo_generate_sitemap_task():
    from project.services.seo import generate_sitemap

    try:
        generate_sitemap()
    except Exception:
        logger.exception("Failed seo_generate_sitemap_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    name="project.celery_tasks.generate_robots_txt_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_robots_txt_task():
    from project.services.seo import generate_robots_txt

    try:
        generate_robots_txt()
    except Exception:
        logger.exception("Failed generate_robots_txt_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()
