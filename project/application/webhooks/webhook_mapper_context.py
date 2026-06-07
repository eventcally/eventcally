from project.application.webhooks.abstract_url_provider import AbstractUrlProvider
from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)


class WebhookMapperContext(AbstractWebhookMapperContext):
    def __init__(self, url_provider: AbstractUrlProvider):
        self.url_provider = url_provider

    def get_image_url(self, image_id: int, image_hash: int) -> str:
        return self.url_provider.get_image_url(image_id, image_hash)
