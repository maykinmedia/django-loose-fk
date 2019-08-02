from django.apps import AppConfig

from rest_framework import serializers

from . import drf, fields


class DjangoLooseFkConfig(AppConfig):
    name = "django_loose_fk"

    def ready(self) -> None:
        register_serializer_field()


def register_serializer_field() -> None:
    mapping = serializers.ModelSerializer.serializer_field_mapping
    mapping[fields.FkOrURLField] = drf.FKOrURLField
