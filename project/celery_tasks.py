from celery.schedules import crontab

from project import celery


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=0, minute=0), clear_images_task)
    sender.add_periodic_task(crontab(hour=0, minute=5), clear_admin_unit_dumps_task)
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
