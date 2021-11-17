from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.inspectors.field import get_basic_type_info

from django_loose_fk.inspectors.query import FilterInspector
from testapp.api import ZaakObjectViewSet, ZaakSerializer, ZaakViewSet


def test_type_info():
    field = ZaakSerializer().fields["zaaktype"]

    type_info = get_basic_type_info(field)

    assert type_info == {
        "type": openapi.TYPE_STRING,
        "format": openapi.FORMAT_URI,
        "min_length": 1,
    }


def test_filter_introspection():
    viewset = ZaakViewSet()
    inspector = FilterInspector(viewset, "/foo", "get", [], None)
    filter_backend = DjangoFilterBackend()

    parameters = inspector.get_filter_parameters(filter_backend)

    assert len(parameters) == 2

    zaaktype_param = parameters[0]
    assert zaaktype_param.name == "zaaktype"
    assert zaaktype_param.type == openapi.TYPE_STRING
    assert zaaktype_param.format == openapi.FORMAT_URI

    zaaktype_in_param = parameters[1]
    assert zaaktype_in_param.name == "zaaktype__in"
    assert zaaktype_in_param.type == openapi.TYPE_STRING
    assert zaaktype_in_param.format == openapi.FORMAT_URI


def test_declared_filter_introspection():
    viewset = ZaakObjectViewSet()
    inspector = FilterInspector(viewset, "/foo", "get", [], None)
    filter_backend = DjangoFilterBackend()

    parameters = inspector.get_filter_parameters(filter_backend)

    assert len(parameters) == 1
    param = parameters[0]

    assert param.name == "zaak"
    assert param.type == openapi.TYPE_STRING
    assert param.format == openapi.FORMAT_URI
