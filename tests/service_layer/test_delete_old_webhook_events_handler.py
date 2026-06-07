import datetime

from tests.base_test import BaseTest


class TestDeleteOldWebhookEventsHandler(BaseTest):
    def test_delete_old_webhook_events(self, app, client, seeder, utils):
        from project.application import commands
        from project.domain.models.aggregates.webhook_event_aggregate import (
            WebhookEventAggregate,
        )
        from project.domain.models.entities.actor import Actor
        from project.models.webhook_event import WebhookEvent

        # Arrange: Create webhook events - some old, some new
        message_bus = app.container.cqrs.message_bus()
        uow = message_bus.create_uow()

        with app.app_context():
            with uow:
                # Old event (5 days ago)
                old_event = WebhookEventAggregate.model_construct(id=-1)
                old_event.timestamp = datetime.datetime.now(
                    datetime.UTC
                ) - datetime.timedelta(days=5)
                old_event.event_type = "test.old"
                old_event.payload = {"data": "old event"}
                uow.webhook_events.add(old_event)

                # Recent event (1 day ago)
                recent_event = WebhookEventAggregate.model_construct(id=-1)
                recent_event.timestamp = datetime.datetime.now(
                    datetime.UTC
                ) - datetime.timedelta(days=1)
                recent_event.event_type = "test.recent"
                recent_event.payload = {"data": "recent event"}
                uow.webhook_events.add(recent_event)

                uow.commit()

            # Act: Delete old events (older than 3 days)
            cmd = commands.DeleteOldWebhookEventsCommand(actor=Actor())
            deleted_count = message_bus.handle(cmd)

            # Assert: Old event deleted, recent event remains
            with uow:
                all_events = uow.session.query(WebhookEvent).all()
                assert len(all_events) == 1
                assert all_events[0].event_type == "test.recent"
                assert deleted_count == 1
