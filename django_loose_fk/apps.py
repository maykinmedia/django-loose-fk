from django.apps import AppConfig

from rest_framework import serializers

from . import drf, fields, filters

try:
    import drf_yasg
except ImportError:
    drf_yasg = None


class DjangoLooseFkConfig(AppConfig):
    name = "django_loose_fk"

    def ready(self) -> None:
        from . import checks  # noqa
        from . import lookups  # noqa

        register_serializer_field()
        filters.register_field_default()
        register_yasg_fields()


def register_serializer_field() -> None:
    mapping = serializers.ModelSerializer.serializer_field_mapping
    mapping[fields.FkOrURLField] = drf.FKOrURLField


def register_yasg_fields() -> None:
    # no drf yasg installed
    if drf_yasg is None:
        return

    from drf_yasg import openapi
    from drf_yasg.inspectors.field import basic_type_info

    # since it subclasses basic types present, we need to get the most specific
    # classes hit first
    type_info = (openapi.TYPE_STRING, openapi.FORMAT_URI)
    basic_type_info.insert(0, (fields.FkOrURLField, type_info))
    basic_type_info.insert(0, (drf.FKOrURLField, type_info))
