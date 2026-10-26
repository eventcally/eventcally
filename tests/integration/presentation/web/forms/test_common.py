def test_base64_image_form_populate_obj_clears_when_no_image(app):
    from project.infrastructure.models import Image
    from project.presentation.web.forms.common import Base64ImageForm

    with app.test_request_context():
        form = Base64ImageForm(meta={"csrf": False})
        form.image_base64.image_data = None
        form.image_base64.encoding_format = None

        obj = Image(data=b"x", encoding_format="image/png", copyright_text="EventCally")
        form.populate_obj(obj)

        assert obj.data is None
        assert obj.encoding_format is None


def test_base64_image_form_populate_obj_sets_image_data(app):
    from project.infrastructure.models import Image
    from project.presentation.web.forms.common import Base64ImageForm

    with app.test_request_context():
        form = Base64ImageForm(meta={"csrf": False})
        form.image_base64.image_data = b"new-image-bytes"
        form.image_base64.encoding_format = "image/png"

        obj = Image()
        form.populate_obj(obj)

        assert obj.data == b"new-image-bytes"
        assert obj.encoding_format == "image/png"


def _image_form(app, seeder, **data):
    from project.presentation.web.forms.common import Base64ImageForm

    form_data = {"image_base64": seeder.get_default_image_upload_base64()}
    form_data.update(data)

    with app.test_request_context(method="POST", data=form_data):
        from flask import request

        form = Base64ImageForm(request.form, meta={"csrf": False})
        return form, form.validate()


def test_base64_image_form_validate_accepts_image(app, seeder):
    form, valid = _image_form(app, seeder, copyright_text="EventCally")

    assert valid
    assert form.image_base64.image_data
    assert form.image_base64.encoding_format == "image/png"


def test_base64_image_form_validate_requires_copyright(app, seeder):
    form, valid = _image_form(app, seeder, copyright_text=" ")

    assert not valid
    assert form.copyright_text.errors


def test_base64_image_form_validate_rejects_invalid_image(app, seeder):
    form, valid = _image_form(
        app, seeder, image_base64="nonsense", copyright_text="EventCally"
    )

    assert not valid
    assert form.image_base64.errors
    assert form.image_base64.image_data is None


def test_ajax_select_field_without_value_clears_when_blank_allowed(app):
    from project.presentation.web.forms.common import Base64ImageForm

    with app.test_request_context():
        form = Base64ImageForm(meta={"csrf": False})
        form.license.process_formdata([])

        assert form.license.data is None
