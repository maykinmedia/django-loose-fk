from dataclasses import dataclass

from django.db import models
from django.db.models.base import ModelBase

try:
    import requests
except ImportError:

    def _get(*args, **kwargs):
        raise ImportError("You need to install the 'requests' library")

    requests = object()
    requests.get = _get


def forbidden_save(*args, **kwargs):
    raise RuntimeError("Saving remotely fetched objects is forbidden.")


@dataclass
class RequestsLoader:
    url: str
    model: ModelBase

    def load(self) -> models.Model:
        # TODO: use a serializer layer in between
        data = requests.get(self.url).json()
        del data["url"]
        instance = self.model(**data)
        # replace the save function so that it is blocked - prevents
        # accidentally persisting remote objects to local database
        instance.save = forbidden_save
        return instance
