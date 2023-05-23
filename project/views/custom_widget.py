from project import app


@app.route("/custom_widget/<string:type>")
def custom_widget_type(type: str):
    env = app.jinja_env.overlay(variable_start_string="[%", variable_end_string="%]")
    template = env.get_template(f"custom_widget/{type}.html")
    return template.render()
