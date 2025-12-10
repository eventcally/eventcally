from project import db
from project.models.custom_widget_generated import CustomWidgetGeneratedMixin


class CustomWidget(db.Model, CustomWidgetGeneratedMixin):
    pass
