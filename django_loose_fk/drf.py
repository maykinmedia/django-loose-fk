"""
Django Rest Framework integration.

Provides a custom field.
"""
import logging
from dataclasses import dataclass
from typing import Tuple, Union
from urllib.parse import ParseResult, urlparse

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator as _URLValidator
from django.db import models
from django.db.models.base import ModelBase
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from rest_framework import fields, serializers
from rest_framework.utils.model_meta import get_field_info

from .fields import FkOrURLField, InstanceOrUrl
from .loaders import FetchError, FetchJsonError
from .utils import get_resource_for_path

logger = logging.getLogger(__name__)


# django tests use testserver host, but that doesn't pass core URLValidation
# regex...
class URLValidator(_URLValidator):
    def __call__(self, value):
        if value.startswith("http://testserver/"):
            return
        super().__call__(value)


@dataclass
class Resolver:
    """
    Resolve URLs to remote or local objects.
    """

    model: ModelBase
    field: FkOrURLField

    def resolve(self, host: str, url: str) -> models.Model:
        parsed = urlparse(url)
        is_local = parsed.netloc == host
        return self.resolve_local(parsed) if is_local else self.resolve_remote(url)

    def resolve_local(self, parsed: ParseResult) -> models.Model:
        return get_resource_for_path(parsed.path)

    def resolve_remote(self, url: str) -> models.Model:
        # load the remote object
        instance = self.model(**{self.field.name: url})
        return getattr(instance, self.field.name)


class FKOrURLValidator:
    """
    Validate that the URL is a valid remote object or local FK.
    """

    message = _(
        'Bad URL "{url}" - object could not be fetched. '
        "This *may* be because you have insufficient read permissions."
    )

    def __init__(self, code=None):
        self.code = code or "bad-url"

    def set_context(self, serializer_field):
        model, field = serializer_field._get_model_and_field()
        self.resolver = Resolver(model, field)
        self.host = serializer_field.context["request"].get_host()
        serializer_field.context["resolver"] = self.resolver

    def __call__(self, url: str):
        assert isinstance(
            url, str
        ), "You must use HyperlinkedRelatedField for the local FKs"

        url_validator = URLValidator()
        try:
            url_validator(url)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message, code=self.code)

        try:
            self.resolver.resolve(self.host, url)
        except FetchError as exc:  # remote resolution fails
            logger.info("Could not fetch %s: %r", url, exc, exc_info=exc)
            raise serializers.ValidationError(
                self.message.format(url=url), code="bad-url"
            )
        except FetchJsonError as exc:
            logger.info(
                "URL %s doesn't seem to point to a JSON endpoint: %r",
                url,
                exc,
                exc_info=exc,
            )
            raise serializers.ValidationError(
                self.message.format(url=url), code="invalid-resource"
            )
        except (Http404, models.ObjectDoesNotExist):  # local resolution fails
            logger.info("Local lookup for %s didn't resolve to an object.", url)
            raise serializers.ValidationError(
                self.message.format(url=url), code="does_not_exist"
            )


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

    default_error_messages = {"invalid": _("Enter a valid URL.")}

    def __init__(self, *args, **kwargs):
        self.lookup_field = kwargs.pop("lookup_field", None)
        super().__init__(*args, **kwargs)

        self.validators += [FKOrURLValidator()]

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

    def run_validation(self, *args, **kwargs) -> Union[models.Model, None]:
        url = super().run_validation(*args, **kwargs)

        if url is None:
            # see rest_framework.fields.Field.validate_empty_values
            return None

        host = self.context["request"].get_host()
        resolver = self.context["resolver"]
        return resolver.resolve(host, url)

    def to_representation(self, value: InstanceOrUrl) -> str:
        if isinstance(value, str):
            return super().to_representation(value)

        model_class, model_field = self._get_model_and_field()

        # check if it's a local FK, in that case, use the HyperlinkedRelatedField
        # to serialize the value
        if value.pk is not None:
            info = get_field_info(model_class)
            fk_field_name = model_field.fk_field

            extra_field_kwargs = self.parent.get_extra_kwargs().get(self.field_name, {})
            field_class, field_kwargs = self.parent.build_field(
                fk_field_name, info, model_class, 0
            )
            field_kwargs = self.parent.include_extra_kwargs(
                field_kwargs, extra_field_kwargs
            )
            field_kwargs.pop("max_length", None)
            field_kwargs.pop("min_length", None)
            _field = field_class(**field_kwargs)
            _field.parent = self.parent
            return _field.to_representation(value)
        else:
            # TODO: this breaks if there is no serializer instance, but just
            # raw data
            url_field_name = model_field.url_field
            return getattr(self.parent.instance, url_field_name)
