from typing import Type

from django.conf import settings
from django.core.signals import setting_changed
from django.db import models
from django.db.models.base import ModelBase
from django.utils.functional import LazyObject, empty
from django.utils.module_loading import import_string

from .virtual_models import get_model_instance

SETTING = "DEFAULT_LOOSE_FK_LOADER"


class BaseLoader:
    @staticmethod
    def fetch_object(url: str):
        raise NotImplementedError

    def load(self, url: str, model: ModelBase) -> models.Model:
        # TODO: use a serializer layer in between
        data = self.fetch_object(url)
        return get_model_instance(model, data, loader=self)


class RequestsLoader(BaseLoader):
    @staticmethod
    def fetch_object(url: str) -> dict:
        import requests

        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def get_loader_class() -> Type[BaseLoader]:
    import_path = getattr(settings, SETTING, "django_loose_fk.loaders.RequestsLoader")
    return import_string(import_path)


class DefaultLoader(LazyObject):
    def __init__(self):
        super().__init__()

        setting_changed.connect(self._reset)

    def _reset(self, setting, **kwargs):
        if setting != SETTING:
            return
        self._wrapped = empty

    def _setup(self):
        self._wrapped = get_loader_class()()


default_loader = DefaultLoader()
