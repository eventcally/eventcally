"""Celery task names are a wire contract: messages already queued in Redis, the beat
schedule and a rolling deploy (old web + new worker or vice versa) address tasks by
name. This freezes the pre-refactor names."""

from unittest.mock import Mock

from project.application import commands
from project.domain.models.entities.actor import Actor

LEGACY_TASK_NAMES = frozenset(
    {
        "project.base_tasks.send_mail_with_body_task",
        "project.base_tasks.process_delayed_event",
        "project.base_tasks.process_delayed_event_v2",
        "project.base_tasks.process_delayed_command",
        "project.base_tasks.process_delayed_command_v2",
        "project.celery_tasks.delete_old_webhook_events_task",
        "project.celery_tasks.clear_images_task",
        "project.celery_tasks.update_recurring_dates_task",
        "project.celery_tasks.dump_all_task",
        "project.celery_tasks.dump_admin_unit_task",
        "project.celery_tasks.clear_admin_unit_dumps_task",
        "project.celery_tasks.delete_admin_units_with_due_request_task",
        "project.celery_tasks.delete_admin_unit_task",
        "project.celery_tasks.delete_user_with_due_request_task",
        "project.celery_tasks.delete_ghost_users_task",
        "project.celery_tasks.delete_old_events_task",
        "project.celery_tasks.delete_user_task",
        "project.celery_tasks.delete_ghost_user_task",
        "project.celery_tasks.delete_event_task",
        "project.celery_tasks.seo_generate_sitemap_task",
        "project.celery_tasks.generate_robots_txt_task",
    }
)


def test_registered_task_names_are_frozen(app):
    from project.infrastructure.celery_app import celery

    registered = {n for n in celery.tasks if not n.startswith("celery.")}

    assert registered == LEGACY_TASK_NAMES


def test_periodic_tasks_use_frozen_names(app):
    from project.celery_tasks import setup_periodic_tasks

    sender = Mock()
    setup_periodic_tasks(sender=sender)

    calls = sender.add_periodic_task.call_args_list
    assert len(calls) == 11
    assert {c.args[1].name for c in calls} <= LEGACY_TASK_NAMES
    assert len({c.args[1].name for c in calls}) == 11
    schedules = {c.args[1].name.rsplit(".", 1)[1]: c.args[0] for c in calls}
    assert (
        schedules["clear_images_task"].hour,
        schedules["clear_images_task"].minute,
    ) == ({0}, {0})
    assert (
        schedules["generate_robots_txt_task"].hour,
        schedules["generate_robots_txt_task"].minute,
    ) == ({4}, {0})


def test_legacy_name_lookup_executes(app, db):
    from project.infrastructure.celery_app import celery

    command = commands.DeleteOldWebhookEventsCommand(actor=Actor())
    path = f"{command.__class__.__module__}.{command.__class__.__name__}"
    task = celery.tasks["project.base_tasks.process_delayed_command_v2"]

    with app.app_context():
        result = task.apply(args=[path, command.model_dump_json(exclude_unset=True)])

    assert result.successful()


def test_celery_main_is_project(app):
    from project.infrastructure.celery_app import celery

    assert celery.main == "project"
