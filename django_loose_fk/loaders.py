import json
from typing import Type

from django.conf import settings
from django.core.signals import setting_changed
from django.db import models
from django.db.models.base import ModelBase
from django.utils.functional import LazyObject, empty
from django.utils.module_loading import import_string

from .virtual_models import get_model_instance

SETTING = "DEFAULT_LOOSE_FK_LOADER"


class FetchError(Exception):
    pass


class FetchJsonError(Exception):
    pass


class BaseLoader:
    @staticmethod
    def fetch_object(url: str):
        raise NotImplementedError  # noqa

    def load(self, url: str, model: ModelBase) -> models.Model:
        # TODO: use a serializer layer in between
        data = self.fetch_object(url)
        return get_model_instance(model, data, loader=self)


class RequestsLoader(BaseLoader):
    @staticmethod
    def fetch_object(url: str) -> dict:
        import requests

        response = requests.get(url)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise FetchError(exc.args[0]) from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise FetchJsonError(exc.args[0]) from exc

        return data


def get_loader_class() -> Type[BaseLoader]:
    import_path = getattr(settings, SETTING, "django_loose_fk.loaders.RequestsLoader")
    return import_string(import_path)


class DefaultLoader(LazyObject):
    def __init__(self):
        super().__init__()

        setting_changed.connect(self._reset)

    def _reset(self, setting, **kwargs):
        if setting != SETTING:
            return  # noqa
        self._wrapped = empty

    def _setup(self):
        self._wrapped = get_loader_class()()


default_loader = DefaultLoader()
