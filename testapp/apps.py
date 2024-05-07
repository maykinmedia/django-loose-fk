from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = "testapp"

    def ready(self):
        from django_loose_fk import oas_extensions  # noqa
