from functools import lru_cache
from typing import Any, Dict

from django.apps import apps
from django.db import models
from django.db.models.base import ModelBase


def get_model_instance(model: ModelBase, data: Dict[str, Any], loader) -> models.Model:
    # loop over the model fields, extract the data and convert it to the appropriate
    # python type
    model_data = {}
    for field in model._meta.get_fields():
        if field.auto_created:
            continue

        # nothing to do for this field if it's not present in the data offered
        if field.name not in data:
            continue

        # ensure the raw input is cast to the right data type
        model_data[field.name] = field.to_python(data[field.name])

    virtual_model = virtual_model_factory(model, loader=loader)
    return virtual_model(url=data.get("url"), initial_data=data, **model_data)


class VirtualModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        from .handlers import HANDLERS

        loader = attrs.pop("_loose_fk_loader")
        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        for field in new_cls._meta.get_fields():
            if field.auto_created:
                continue

            Handler = HANDLERS.get(type(field))
            if not Handler:
                continue

            handler = Handler(
                field.name, loader=loader, remote_model=field.related_model
            )
            # install new descriptor
            setattr(new_cls, field.name, handler)

        return new_cls


class ProxyMixin:
    def __init__(self, url: str, initial_data: dict, *args, **kwargs):
        self._loose_fk_data = {"url": url}
        self._initial_data = initial_data
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, str):  # compare URLs
            return self._loose_fk_data["url"] == other

        elif isinstance(other, ProxyMixin):
            return self._loose_fk_data["url"] == other._loose_fk_data["url"]

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
