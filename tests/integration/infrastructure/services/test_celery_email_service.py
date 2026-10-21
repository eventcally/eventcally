import pytest

from project.application.services.abstract_mail_sender import AbstractMailSender
from project.infrastructure.services.celery_email_service import CeleryEmailService


class _RecordingMailSender(AbstractMailSender):
    def __init__(self):
        self.calls = []

    def send_mails_with_body(self, recipients, subject, body, html):
        self.calls.append((recipients, subject, body, html))


def test_send_mails_with_signatures_sends_single_mails(app):
    sender = _RecordingMailSender()
    service = CeleryEmailService(
        default_locale="de",
        localization_service=app.container.infrastructure.localization_service(),
        template_render_service=app.container.infrastructure.template_render_service(),
        mail_sender=sender,
    )

    service.send_mails_with_signatures(
        [("a@test.de", "S1", "B1", "<p>B1</p>"), ("b@test.de", "S2", "B2", "<p>B2</p>")]
    )

    assert sender.calls == [
        (["a@test.de"], "S1", "B1", "<p>B1</p>"),
        (["b@test.de"], "S2", "B2", "<p>B2</p>"),
    ]


def _service(app):
    return CeleryEmailService(
        default_locale="de",
        localization_service=app.container.infrastructure.localization_service(),
        template_render_service=app.container.infrastructure.template_render_service(),
        mail_sender=_RecordingMailSender(),
    )


@pytest.fixture
def set_eager():
    from project.infrastructure.celery_app import celery

    previous = celery.conf.task_always_eager

    def _set(value):
        celery.conf.task_always_eager = value

    yield _set
    celery.conf.task_always_eager = previous


def test_tracked_without_signatures_has_nothing_to_track(app):
    job = _service(app).send_mails_with_signatures_tracked([])

    assert (job.job_id, job.count) == (None, 0)


def test_tracked_eager_has_no_job_id(app, mocker, set_eager):
    set_eager(True)
    group = mocker.patch("celery.group")

    job = _service(app).send_mails_with_signatures_tracked(
        [("a@test.de", "S1", "B1", "<p>B1</p>")]
    )

    group.return_value.delay.assert_called_once()
    group.return_value.delay.return_value.save.assert_not_called()
    assert (job.job_id, job.count) == (None, 1)


def test_tracked_saves_the_group_result(app, mocker, set_eager):
    set_eager(False)
    group = mocker.patch("celery.group")
    result = group.return_value.delay.return_value
    result.id = "group-1"

    job = _service(app).send_mails_with_signatures_tracked(
        [("a@test.de", "S1", "B1", "<p>B1</p>"), ("b@test.de", "S2", "B2", "<p>B2</p>")]
    )

    result.save.assert_called_once()
    assert (job.job_id, job.count) == ("group-1", 2)
