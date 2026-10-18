import datetime

from sqlalchemy import text


def _age(app, db, statement, days, **params):
    with app.app_context():
        db.session.execute(
            text(statement),
            {"when": datetime.datetime.utcnow() - datetime.timedelta(days=days)}
            | params,
        )
        db.session.commit()


def _exists(app, db, model, id):
    with app.app_context():
        return db.session.get(model, id) is not None


def test_delete_admin_unit_task(client, seeder, app, db):
    from project.celery_tasks import delete_admin_unit_task
    from project.infrastructure.models import AdminUnit

    owner_id = seeder.create_user()
    old_id = seeder.create_admin_unit(owner_id, "Old")
    fresh_id = seeder.create_admin_unit(owner_id, "Fresh")
    stmt = "UPDATE adminunit SET deletion_requested_at = :when WHERE id = :id"
    _age(app, db, stmt, 4, id=old_id)
    _age(app, db, stmt, 1, id=fresh_id)

    with app.app_context():
        delete_admin_unit_task(old_id)
        delete_admin_unit_task(fresh_id)
        delete_admin_unit_task(99999)

    assert not _exists(app, db, AdminUnit, old_id)
    assert _exists(app, db, AdminUnit, fresh_id)


def test_delete_user_task(client, seeder, app, db):
    from project.celery_tasks import delete_user_task
    from project.infrastructure.models import User

    due_id = seeder.create_user("due@test.de")
    cancelled_id = seeder.create_user("cancelled@test.de")
    stmt = 'UPDATE "user" SET deletion_requested_at = :when WHERE id = :id'
    _age(app, db, stmt, 4, id=due_id)

    with app.app_context():
        delete_user_task(due_id)
        delete_user_task(cancelled_id)
        delete_user_task(99999)

    assert not _exists(app, db, User, due_id)
    assert _exists(app, db, User, cancelled_id)


def test_delete_ghost_user_task(client, seeder, app, db):
    from project.celery_tasks import delete_ghost_user_task
    from project.infrastructure.models import User

    ghost_id = seeder.create_user("ghost@test.de", confirm=False)

    with app.app_context():
        delete_ghost_user_task(ghost_id)
        delete_ghost_user_task(99999)

    assert not _exists(app, db, User, ghost_id)


def test_delete_event_task(client, seeder, app, db):
    from project.celery_tasks import delete_event_task
    from project.infrastructure.models import Event, EventDate

    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=3")

    with app.app_context():
        assert db.session.query(EventDate).filter_by(event_id=event_id).count() == 3
        delete_event_task(event_id)
        delete_event_task(99999)

    assert not _exists(app, db, Event, event_id)
    with app.app_context():
        assert db.session.query(EventDate).filter_by(event_id=event_id).count() == 0


def test_delete_ghost_users_task_fans_out_to_ghost_task(client, seeder, app, mocker):
    import project.celery_tasks as celery_tasks

    ghost_id = seeder.create_user("ghost@test.de", confirm=False)
    mocker.patch.object(celery_tasks, "group")
    ghost_s = mocker.patch.object(celery_tasks.delete_ghost_user_task, "s")
    user_s = mocker.patch.object(celery_tasks.delete_user_task, "s")
    mocker.patch.object(
        celery_tasks,
        "_query_bus",
        return_value=mocker.Mock(handle=mocker.Mock(return_value=[ghost_id])),
    )

    with app.app_context():
        celery_tasks.delete_ghost_users_task()
        # the generator passed to group() is lazy; consume it
        list(celery_tasks.group.call_args[0][0])

    ghost_s.assert_called_once_with(ghost_id)
    user_s.assert_not_called()
