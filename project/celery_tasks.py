from celery import group
from celery.schedules import crontab

from project import celery


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
    sender.add_periodic_task(crontab(hour=1, minute=0), update_recurring_dates_task)
    sender.add_periodic_task(crontab(hour=2, minute=0), dump_all_task)
    sender.add_periodic_task(crontab(hour=3, minute=0), seo_generate_sitemap_task)
    sender.add_periodic_task(crontab(hour=4, minute=0), generate_robots_txt_task)


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def clear_images_task():
    from project.services.cache import clear_images

    clear_images()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def update_recurring_dates_task():
    from project import app, db
    from project.services.event import update_recurring_dates

    try:
        update_recurring_dates()
    except Exception:
        app.logger.exception("Failed update_recurring_dates_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_all_task():
    from project import app, db
    from project.services.dump import dump_all

    try:
        dump_all()
    except Exception:
        app.logger.exception("Failed dump_all_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_admin_unit_task(admin_unit_id):
    from project import app, db
    from project.services.dump import dump_admin_unit

    try:
        dump_admin_unit(admin_unit_id)
    except Exception:
        app.logger.exception(f"Failed dump_admin_unit_task {admin_unit_id}")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def clear_admin_unit_dumps_task():
    from project.services.dump import clear_admin_unit_dumps

    clear_admin_unit_dumps()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_admin_units_with_due_request_task():
    from project import app, db
    from project.services.admin_unit import get_admin_units_with_due_delete_request

    try:
        admin_units = get_admin_units_with_due_delete_request()

        if not admin_units:
            return

        group(
            delete_admin_unit_task.s(admin_unit.id) for admin_unit in admin_units
        ).delay()
    except Exception:
        app.logger.exception("Failed delete_admin_units_with_due_request_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_admin_unit_task(admin_unit_id):
    from project import app, db
    from project.models import AdminUnit

    try:
        admin_unit = db.session.get(AdminUnit, admin_unit_id)

        if admin_unit:
            db.session.delete(admin_unit)
            db.session.commit()
            app.logger.info(f"Delete admin unit {admin_unit_id}")
    except Exception:
        app.logger.exception(f"Failed to delete admin unit {admin_unit_id}")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_with_due_request_task():
    from project import app, db
    from project.services.user import get_users_with_due_delete_request

    try:
        users = get_users_with_due_delete_request()

        if not users:
            return

        group(delete_user_task.s(user.id) for user in users).delay()
    except Exception:
        app.logger.exception("Failed delete_user_with_due_request_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_ghost_users_task():
    from project import app, db
    from project.services.user import get_ghost_users

    try:
        users = get_ghost_users()

        if not users:
            return

        group(delete_user_task.s(user.id) for user in users).delay()
    except Exception:
        app.logger.exception("Failed delete_ghost_users_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_old_events_task():
    from project import app, db
    from project.services.event import get_old_events

    try:
        events = get_old_events()

        if not events:
            return

        group(delete_event_task.s(event.id) for event in events).delay()
    except Exception:
        app.logger.exception("Failed delete_old_events_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_task(user_id):
    from project import app, db
    from project.models import User

    try:
        user = db.session.get(User, user_id)

        if user:
            db.session.delete(user)
            db.session.commit()
            app.logger.info(f"Deleted user {user_id}")
    except Exception:
        app.logger.exception(f"Failed to delete user {user_id}")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_event_task(event_id):
    from project import app, db
    from project.models import Event

    try:
        event = db.session.get(Event, event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
            app.logger.info(f"Deleted event {event_id}")
    except Exception:
        app.logger.exception(f"Failed to delete event {event_id}")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def seo_generate_sitemap_task():
    from project import app, db
    from project.services.seo import generate_sitemap

    try:
        generate_sitemap(app.config["SEO_SITEMAP_PING_GOOGLE"])
    except Exception:
        app.logger.exception("Failed seo_generate_sitemap_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_robots_txt_task():
    from project import app, db
    from project.services.seo import generate_robots_txt

    try:
        generate_robots_txt()
    except Exception:
        app.logger.exception("Failed generate_robots_txt_task")
        db.session.rollback()
        raise
    finally:
        db.session.close()
