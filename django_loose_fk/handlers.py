from typing import Any, Dict, List, Union

from django.db import models
from django.db.models.base import ModelBase

from .fields import FkOrURLField
from .query_list import QueryList

DictOrUrl = Union[Dict[str, Any], str]


class BaseHandler:
    def __init__(self, field_name: str, loader, remote_model: ModelBase):
        self.field_name = field_name
        self.loader = loader
        self.remote_model = remote_model

    def __set__(self, instance: models.Model, value: List[DictOrUrl]):
        instance._loose_fk_data[self.field_name] = value


class M2MHandler(BaseHandler):
    def __get__(self, instance, cls=None) -> QueryList:
        raw_data = instance._loose_fk_data.get(self.field_name, [])
        assert all((isinstance(url, str) for url in raw_data))

        loaded_data = [
            self.loader.load(url=url, model=self.remote_model) for url in raw_data
        ]

        return QueryList(loaded_data)


class FKHandler(BaseHandler):
    def __get__(self, instance, cls=None) -> models.Model:
        raw_data = instance._loose_fk_data.get(self.field_name, None)
        if raw_data is None:
            return None
        assert isinstance(raw_data, str)
        return self.loader.load(url=raw_data, model=self.remote_model)


class FkOrURLHandler(BaseHandler):
    def __get__(self, instance, cls=None):
        raw_data = instance._loose_fk_data.get(self.field_name, None)
        if raw_data is None:
            return None

        # similar to FKHandler load the modal instance but only if it's a local url
        if isinstance(raw_data, str) and self.loader.is_local_url(raw_data):
            return self.loader.load(url=raw_data, model=self.remote_model)

        return raw_data


HANDLERS = {
    models.ForeignKey: FKHandler,
    models.ManyToManyField: M2MHandler,
    FkOrURLField: FkOrURLHandler,
}
