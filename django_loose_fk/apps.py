from django.apps import AppConfig

from rest_framework import serializers

from . import drf, fields, filters


class DjangoLooseFkConfig(AppConfig):
    name = "django_loose_fk"

    def ready(self) -> None:
        from . import checks  # noqa
        from . import lookups  # noqa

        register_serializer_field()
        filters.register_field_default()


def register_serializer_field() -> None:
    mapping = serializers.ModelSerializer.serializer_field_mapping
    mapping[fields.FkOrURLField] = drf.FKOrURLField
