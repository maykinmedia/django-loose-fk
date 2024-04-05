"""
Filter support for django-filter.
"""

import logging
from urllib.parse import urlparse

from django import forms
from django.db.models import Q

import django_filters
from django_filters.filterset import FilterSet, remote_queryset as _remote_queryset

from .fields import FkOrURLField
from .utils import get_resource_for_path, get_subclasses, is_local

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

        values = value
        if not isinstance(values, list):
            values = [values]

        parsed_values = [urlparse(value) for value in values]
        host = self.parent.request.get_host()
        model_field = self.model._meta.get_field(self.field_name)

        filters = self.get_filters(model_field, parsed_values, host)

        # In case the query contained both local and remote zaaktypen, then the filters dict will be
        # {'_zaaktype__in': ['url'], 'externe_zaaktype__in': ['url']}. These filters need to be OR'd
        complex_filter = Q()
        for lookup, value in filters.items():
            complex_filter |= Q(**{lookup: value})

        qs = self.get_method(qs)(complex_filter)
        return qs.distinct() if self.distinct else qs

    def get_filters(self, model_field, parsed_values, host) -> dict:
        local_filter_key = f"{model_field.fk_field}__{self.lookup_expr}"
        external_filter_key = f"{model_field.url_field}__{self.lookup_expr}"

        filters = {}
        for value in parsed_values:
            local = is_local(host, value.geturl())
            if local:
                local_object = get_resource_for_path(value.path)
                if self.instance_path:
                    for bit in self.instance_path.split("."):
                        local_object = getattr(local_object, bit)
                filter_key = local_filter_key
                filter_value = local_object
            else:
                filter_key = external_filter_key
                filter_value = value.geturl()

            if self.lookup_expr == "in":
                if filter_key in filters:
                    filters[filter_key] += [filter_value]
                else:
                    filters[filter_key] = [filter_value]
            elif self.lookup_expr == "exact":
                filters[filter_key] = filter_value

        return filters
