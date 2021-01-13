def enum_to_properties(self, field, **kwargs):
    """
    Add an OpenAPI extension for marshmallow_enum.EnumField instances
    """
    import marshmallow_enum

    if isinstance(field, marshmallow_enum.EnumField):
        return {"type": "string", "enum": [m.name for m in field.enum]}
    return {}


from project import marshmallow_plugin

marshmallow_plugin.converter.add_attribute_function(enum_to_properties)

import project.api.event.resources
import project.api.event_category.resources
import project.api.event_date.resources
import project.api.image.resources
import project.api.location.resources
import project.api.organization.resources
import project.api.organizer.resources
import project.api.place.resources
