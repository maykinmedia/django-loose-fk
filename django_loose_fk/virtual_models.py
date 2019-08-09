from functools import lru_cache
from typing import Any, Dict, List, Union

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models.base import ModelBase

DictOrUrl = Union[Dict[str, Any], str]


def is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    validator = URLValidator(schemes=["http", "https"])
    try:
        validator(value)
    except ValidationError:
        return False

    return True


def get_model_instance(model: ModelBase, data: Dict[str, Any], loader) -> models.Model:
    field_names = [
        field.name for field in model._meta.get_fields() if not field.auto_created
    ] + ["url"]

    # only keep known fields
    data = {key: value for key, value in data.items() if key in field_names}

    virtual_model = virtual_model_factory(model, loader=loader)
    return virtual_model(**data)


class VirtualModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        loader = attrs.pop("_loose_fk_loader")
        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        for field in new_cls._meta.get_fields():
            if field.auto_created:
                continue

            if not field.is_relation:
                continue

            Handler = HANDLERS[type(field)]
            handler = Handler(
                field.name, loader=loader, remote_model=field.related_model
            )
            # install new descriptor
            setattr(new_cls, field.name, handler)

        return new_cls


class ProxyMixin:
    def __init__(self, url: str, *args, **kwargs):
        self._loose_fk_data = {"url": url}
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, str):  # compare URLs
            return self._loose_fk_data["url"] == other
        return super().__eq__(other)

    def save(self, *args, **kwargs):
        raise RuntimeError("Saving remotely fetched objects is forbidden.")


@lru_cache(maxsize=None)
def virtual_model_factory(model: ModelBase, loader) -> VirtualModelBase:
    class Meta:
        proxy = True

    name = f"Virtual{model.__name__}"
    app_config = apps.get_containing_app_config(model.__module__)

    try:
        model = apps.get_model(app_config.label, name)
    except LookupError:
        pass
    else:
        return model

    Proxy = VirtualModelBase(
        name,
        (ProxyMixin, model),
        {"__module__": model.__module__, "_loose_fk_loader": loader, "Meta": Meta},
    )

    return Proxy


class QueryList:
    def __init__(self, items: list):
        self.items = items

    def __repr__(self):
        return f"<QueryList items={repr(self.items)}>"

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, item):
        # treat URls specially (for now at least)
        if not is_url(item):
            return item in self.items

        urls = (_item._loose_fk_data.get("url") for _item in self.items)
        return item in urls

    def get(self):
        assert len(self.items) == 1
        return self.items[0]

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items

    def count(self):
        return len(self.items)

    def filter(self, *expressions, **filters) -> "QueryList":
        raise NotImplementedError

    def exclude(self, *expressions, **filters) -> "QueryList":
        raise NotImplementedError


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


HANDLERS = {models.ForeignKey: FKHandler, models.ManyToManyField: M2MHandler}
