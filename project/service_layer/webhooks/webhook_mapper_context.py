class WebhookMapperContext:
    def get_image_url(self, image_id: int, image_hash: int) -> str:
        from flask import url_for

        return url_for("main.image", id=image_id, hash=image_hash)
