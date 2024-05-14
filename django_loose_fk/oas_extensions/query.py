"""
Define a filter extension that can handle the custom fields.

Requires drf-spectacular, which can be installed as the [openapi] optional group
dependency.
"""

from drf_spectacular.contrib.django_filters import DjangoFilterExtension

from .. import filters


class LooseFkFilterExtension(DjangoFilterExtension):
    """add "uri" format to loose-fk query params"""

    priority = 1

    def resolve_filter_field(
        self, auto_schema, model, filterset_class, field_name, filter_field
    ):
        schemas = super().resolve_filter_field(
            auto_schema, model, filterset_class, field_name, filter_field
        )

        if isinstance(filter_field, filters.FkOrUrlFieldFilter):
            for schema in schemas:
                if "items" in schema["schema"]:
                    schema["schema"]["items"]["format"] = "uri"
                else:
                    schema["schema"]["format"] = "uri"

        return schemas
