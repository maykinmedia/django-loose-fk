from django.core.exceptions import ValidationError
from django.core.validators import URLValidator as _URLValidator
from django.db import models

from .fields import InstanceOrUrl


class InstanceOrURLValidator(_URLValidator):
    def __call__(self, value: InstanceOrUrl) -> None:
        if isinstance(value, models.Model):
            if value.pk is not None:
                return
            raise ValidationError(self.message, code=self.code)

        assert isinstance(
            value, str
        ), "Expected a string representing a URL to be validated"

        super().__call__(value)
