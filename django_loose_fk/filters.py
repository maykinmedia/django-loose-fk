"""
Filter support for django-filter.
"""
import logging
from urllib.parse import urlparse

from django import forms

import django_filters
from django_filters.filterset import FilterSet, remote_queryset as _remote_queryset

from .fields import FkOrURLField
from .utils import get_resource_for_path, get_subclasses

logger = logging.getLogger(__name__)


def remote_queryset(field: FkOrURLField):
    fk_field = field._fk_field
    return _remote_queryset(fk_field)


def register_field_default():
    for filter_set_class in get_subclasses(FilterSet):
        filter_set_class.FILTER_DEFAULTS.update(
            {
                FkOrURLField: {
                    "filter_class": FkOrUrlFieldFilter,
                    "extra": lambda f: {"queryset": remote_queryset(f)},
                }
            }
        )


class FkOrUrlFieldFilter(django_filters.CharFilter):
    field_class = forms.URLField

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop("queryset")

        # Specified path of attributes that must be traversed to retrieve the
        # desired object
        self.instance_path = kwargs.pop("instance_path", None)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs

        parsed = urlparse(value)
        host = self.parent.request.get_host()

        local = parsed.netloc == host

        # introspect field to build filter
        model_field = self.model._meta.get_field(self.field_name)

        if local:
            local_object = get_resource_for_path(parsed.path)
            if self.instance_path:
                for bit in self.instance_path.split("."):
                    local_object = getattr(local_object, bit)
            filters = {f"{model_field.fk_field}__{self.lookup_expr}": local_object}
        else:
            filters = {f"{model_field.url_field}__{self.lookup_expr}": value}

        qs = self.get_method(qs)(**filters)
        return qs.distinct() if self.distinct else qs
