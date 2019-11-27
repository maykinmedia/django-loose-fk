import json
import warnings
from typing import Type
from urllib.parse import urlparse

from django.conf import settings
from django.core.signals import setting_changed
from django.db import models
from django.db.models.base import ModelBase
from django.http.request import validate_host
from django.utils.functional import LazyObject, empty
from django.utils.module_loading import import_string

from .utils import get_resource_for_path
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

    def is_local_url(self, url: str) -> bool:
        """
        Test if the 'remote' URL is possibly a local URL.

        It's possible that loose-fks are chained - a model has a loose fk to
        a model that has a loose fk itself to another model. When the top and
        last model are local (the middle is remote), then the last model should
        be resolved to the actual instance of that model and not be wrapped
        in a virtual model - which saves a network call.

        Validation if a URL is local is done by looking at the host and
        comparing it against the ALLOWED_HOSTS setting, as Django serves
        those domains.
        """
        allowed_hosts = settings.ALLOWED_HOSTS
        parsed = urlparse(url)

        if any(pattern == "*" for pattern in allowed_hosts):
            warnings.warn(
                "You have wildcards in your ALLOWED_HOSTS setting - "
                "this will cause all remote URLs to be considered local URLs and "
                "break django-loose-fk's behaviour. You should use an explicit list.",
                RuntimeWarning,
            )

        return validate_host(parsed.netloc, allowed_hosts)

    def load_local_object(self, url: str, model: ModelBase) -> models.Model:
        parsed = urlparse(url)
        return get_resource_for_path(parsed.path)

    def load(self, url: str, model: ModelBase) -> models.Model:
        if self.is_local_url(url):
            return self.load_local_object(url, model)

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
