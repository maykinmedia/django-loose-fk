"""
Define a field extension that can handle the custom fields.

Requires drf-spectacular, which can be installed as the [openapi] optional group
dependency.
"""

from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class LooseFkFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "django_loose_fk.drf.FKOrURLField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        default_schema = auto_schema._map_serializer_field(
            self.target, direction, bypass_extensions=True
        )

        return {
            **default_schema,
            "type": "string",
            "format": "uri",
            "minLength": self.target.min_length,
            "maxLength": self.target.max_length,
        }
