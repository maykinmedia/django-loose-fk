"""
Define a query parameters inspector that can handle the custom fields.

Requires drf-yasg, which can be installed as the [openapi] optional group
dependency.
"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_yasg import openapi

from .. import filters

try:
    from vng_api_common.inspectors.query import FilterInspector as BaseFilterInspector
except ImportError:
    from drf_yasg.inspectors.query import CoreAPICompatInspector as BaseFilterInspector


class FilterInspector(BaseFilterInspector):
    def get_filter_parameters(self, filter_backend):
        fields = super().get_filter_parameters(filter_backend)
        if not fields:
            return fields

        if not isinstance(filter_backend, DjangoFilterBackend):
            return fields

        if not hasattr(self.view, "get_queryset"):
            return fields

        queryset = self.view.get_queryset()
        filter_class = filter_backend.get_filterset_class(self.view, queryset)

        for parameter in fields:
            filter_field = filter_class.base_filters.get(parameter.name)
            if not isinstance(filter_field, filters.FkOrUrlFieldFilter):
                continue

            parameter.format = openapi.FORMAT_URI

        return fields
