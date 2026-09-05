from project.application.webhooks.abstract_url_provider import AbstractUrlProvider


class FlaskUrlProvider(AbstractUrlProvider):
    def get_image_url(self, image_id: int, image_hash: int) -> str:
        from flask import url_for

        return url_for("main.image", id=image_id, hash=image_hash)

    def get_site_url(self) -> str:
        from flask import url_for

        return url_for("main.home", _external=True).rstrip("/")
