from flask import current_app

from project.views.main_blueprint import main_bp


@main_bp.route("/custom_widget/<string:type>")
def custom_widget_type(type: str):
    env = current_app.jinja_env.overlay(
        variable_start_string="[%", variable_end_string="%]"
    )
    template = env.get_template(f"custom_widget/{type}.html")
    return template.render()
