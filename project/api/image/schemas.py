from marshmallow import ValidationError, fields, post_load, validates_schema

from project.api import marshmallow
from project.api.schemas import IdSchemaMixin, SQLAlchemyBaseSchema
from project.imageutils import (
    get_bytes_from_image,
    get_image_from_base64_str,
    get_image_from_url,
    get_mime_type_from_image,
    resize_image_to_max,
    validate_image,
)
from project.models import Image


class ImageModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = Image
        load_instance = True


class ImageIdSchema(ImageModelSchema, IdSchemaMixin):
    pass


class ImageBaseSchemaMixin(object):
    copyright_text = marshmallow.auto_field()


class ImageSchema(ImageIdSchema, ImageBaseSchemaMixin):
    image_url = marshmallow.URLFor(
        "image",
        values=dict(id="<id>", s=500),
        metadata={
            "description": "Append query arguments w for width, h for height or s for size(width and height)."
        },
    )


class ImageDumpSchema(ImageModelSchema, ImageBaseSchemaMixin):
    pass


class ImageWriteSchemaMixin(object):
    image_url = fields.String(
        required=False,
        load_only=True,
        allow_none=True,
        metadata={
            "description": "URL to image. Either image_url or image_base64 has to be defined."
        },
    )
    image_base64 = fields.String(
        required=False,
        load_only=True,
        allow_none=True,
        metadata={
            "description": "Base64 encoded image data. Either image_url or image_base64 has to be defined."
        },
    )

    @post_load(pass_original=True)
    def post_load_image_data(self, item, original_data, **kwargs):
        image_url = original_data.get("image_url")
        image_base64 = original_data.get("image_base64")

        if image_url is not None or image_base64 is not None:
            # Mal ist item ein dict und mal ein Image, weil post_load die Reihenfolge der Aufrufe nicht garantieren kann
            if isinstance(item, dict):
                encoding_format, data = self.load_image_data(image_base64, image_url)
                item["encoding_format"] = encoding_format
                item["data"] = data

            elif isinstance(item, Image):
                encoding_format, data = self.load_image_data(image_base64, image_url)
                item.encoding_format = encoding_format
                item.data = data

        return item

    def load_image_data(self, image_base64, image_url):
        image = None

        if image_base64:
            image = get_image_from_base64_str(image_base64)
        elif image_url:
            image = get_image_from_url(image_url)

        if not image:
            return None, None

        validate_image(image)
        resize_image_to_max(image)
        encoding_format = get_mime_type_from_image(image)
        data = get_bytes_from_image(image)
        return encoding_format, data


class ImagePostRequestSchema(
    ImageModelSchema, ImageBaseSchemaMixin, ImageWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()

    @validates_schema
    def validate_image(self, data, **kwargs):
        if data.get("image_url") is None and data.get("image_base64") is None:
            raise ValidationError("Either image_url or image_base64 has to be defined.")


class ImagePatchRequestSchema(
    ImageModelSchema, ImageBaseSchemaMixin, ImageWriteSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()
