from typing import Any, Dict

from django.db import models
from django.db.models.base import ModelBase


def forbidden_save(*args, **kwargs):
    raise RuntimeError("Saving remotely fetched objects is forbidden.")


def get_model_instance(model: ModelBase, data: Dict[str, Any]) -> models.Model:
    fields = {
        field.name: field
        for field in model._meta.get_fields()
        if (field.concrete and not field.auto_created)
    }

    non_relational_data = {
        field_name: value
        for field_name, value in data.items()
        if field_name in fields and not fields[field_name].is_relation
    }

    instance = model(**non_relational_data)

    # replace the save function so that it is blocked - prevents
    # accidentally persisting remote objects to local database
    instance.save = forbidden_save

    return instance
