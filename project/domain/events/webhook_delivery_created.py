from project.domain.types import ObjectId

from .base import Event


class WebhookDeliveryCreated(Event):
    id: ObjectId
