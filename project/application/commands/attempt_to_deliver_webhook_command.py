from project.domain.types import ObjectId

from .base import Command


class AttemptToDeliverWebhookCommand(Command):
    webhook_delivery_id: ObjectId
