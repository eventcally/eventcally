def test_base64_image_form_populate_obj_clears_when_no_image(app):
    from project.forms.common import Base64ImageForm
    from project.models import Image

    with app.test_request_context():
        form = Base64ImageForm(meta={"csrf": False})
        form.image_base64.image_data = None
        form.image_base64.encoding_format = None

        obj = Image(data=b"x", encoding_format="image/png", copyright_text="EventCally")
        form.populate_obj(obj)

        assert obj.data is None
        assert obj.encoding_format is None


def test_base64_image_form_populate_obj_sets_image_data(app):
    from project.forms.common import Base64ImageForm
    from project.models import Image

    with app.test_request_context():
        form = Base64ImageForm(meta={"csrf": False})
        form.image_base64.image_data = b"new-image-bytes"
        form.image_base64.encoding_format = "image/png"

        obj = Image()
        form.populate_obj(obj)

        assert obj.data == b"new-image-bytes"
        assert obj.encoding_format == "image/png"
