from django.core.exceptions import ValidationError
from django.core.validators import URLValidator as _URLValidator
from django.db import models

from .fields import InstanceOrUrl
from .virtual_models import ProxyMixin


class InstanceOrURLValidator(_URLValidator):
    def __call__(self, value: InstanceOrUrl) -> None:
        if isinstance(value, str):  # dealing with a URL
            super().__call__(value)

        if isinstance(value, (ProxyMixin, models.Model)):
            return

        if isinstance(value, models.Model) and value.pk is None:
            raise ValidationError(self.message, code=self.code)
