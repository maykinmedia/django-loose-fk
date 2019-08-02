"""
Django Rest Framework integration.

Provides a custom field.
"""
import logging
from typing import Tuple
from urllib.parse import urlparse

from django.db import models
from django.db.models.base import ModelBase
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from rest_framework import fields
from rest_framework.utils.model_meta import get_field_info

from .fields import FkOrURLField, InstanceOrUrl
from .utils import get_resource_for_path
from .validators import InstanceOrURLValidator

logger = logging.getLogger(__name__)


class FKOrURLField(fields.CharField):
    """
    A serializer field for the database FKOrURLField field.

    * The serialized output is always a URL, either to the local API or the
      remote URL that was registered when saving the instance.
    * The deserialized value is either a string representing a remote URL or a
      local instance of the related model.

    .. warning:: Currently lookups of local instances require you to use
        (Generic) viewsets. It taps into the (view|viewset).get_object() code
        path.
    """

    default_error_messages = {
        "invalid": _("Enter a valid URL."),
        "does_not_exist": _(
            'Invalid URL "{url}" - object does not exist. '
            "This *may* be because you have insufficient read permissions."
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = InstanceOrURLValidator(message=self.error_messages["invalid"])
        self.validators.append(validator)

    def _get_model_and_field(self) -> Tuple[ModelBase, FkOrURLField]:
        model_class = self.parent.Meta.model
        model_field = model_class._meta.get_field(self.source)
        return (model_class, model_field)

    def get_attribute(self, instance: models.Model) -> InstanceOrUrl:
        """
        Optimize fetching the attribute in case it's a remote URL.

        This prevents using the remote fetcher/importer to do network IO when
        it's not needed.
        """
        model_field = self._get_model_and_field()[1]
        url_value = getattr(instance, model_field.url_field)
        if url_value:
            return url_value
        return super().get_attribute(instance)

    def to_internal_value(self, data: str) -> InstanceOrUrl:
        url = super().to_internal_value(data)
        parsed = urlparse(url)

        # test if it's a local URL
        host = self.context["request"].get_host()
        is_local = parsed.netloc == host
        if not is_local:
            return url

        # resolve the path/url...
        try:
            obj = get_resource_for_path(parsed.path)
        except Http404:
            logger.info("Local lookup for %s didn't resolve to an object.", parsed.path)
            self.fail("does_not_exist", url=data)
        return obj

    def to_representation(self, value: InstanceOrUrl) -> str:
        if isinstance(value, str):
            return super().to_representation(value)

        model_class, model_field = self._get_model_and_field()

        # check if it's a local FK, in that case, use the HyperlinkedRelatedField
        # to serialize the value
        if value.pk is not None:
            info = get_field_info(model_class)
            fk_field_name = model_field.fk_field
            field_class, field_kwargs = self.parent.build_field(
                fk_field_name, info, model_class, 0
            )
            _field = field_class(**field_kwargs)
            _field.parent = self.parent
            return _field.to_representation(value)
        else:
            # TODO: this breaks if there is no serializer instance, but just
            # raw data
            url_field_name = model_field.url_field
            return getattr(self.parent.instance, url_field_name)
