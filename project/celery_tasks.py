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
    from project.services.event import update_recurring_dates

    update_recurring_dates()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_all_task():
    from project.services.dump import dump_all

    dump_all()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def dump_admin_unit_task(admin_unit_id):
    from project.services.dump import dump_admin_unit

    dump_admin_unit(admin_unit_id)


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
    from project.services.admin_unit import get_admin_units_with_due_delete_request

    admin_units = get_admin_units_with_due_delete_request()

    if not admin_units:
        return

    group(delete_admin_unit_task.s(admin_unit.id) for admin_unit in admin_units).delay()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_admin_unit_task(admin_unit_id):
    from project.services.admin_unit import delete_admin_unit, get_admin_unit_by_id

    admin_unit = get_admin_unit_by_id(admin_unit_id)

    if not admin_unit:
        return

    delete_admin_unit(admin_unit)


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_with_due_request_task():
    from project.services.user import get_users_with_due_delete_request

    users = get_users_with_due_delete_request()

    if not users:
        return

    group(delete_user_task.s(user.id) for user in users).delay()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_ghost_users_task():
    from project.services.user import get_ghost_users

    users = get_ghost_users()

    if not users:
        return

    group(delete_user_task.s(user.id) for user in users).delay()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_old_events_task():
    from project.services.event import get_old_events

    events = get_old_events()

    if not events:
        return

    group(delete_event_task.s(event.id) for event in events).delay()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_user_task(user_id):
    from project.services.user import delete_user, get_user

    user = get_user(user_id)

    if not user:
        return

    delete_user(user)


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_event_task(event_id):
    from project import db
    from project.models import Event

    event = Event.query.get(event_id)

    if not event:
        return

    db.session.delete(event)
    db.session.commit()


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def seo_generate_sitemap_task():
    from project import app
    from project.services.seo import generate_sitemap

    generate_sitemap(app.config["SEO_SITEMAP_PING_GOOGLE"])


@celery.task(
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_robots_txt_task():
    from project.services.seo import generate_robots_txt

    generate_robots_txt()
