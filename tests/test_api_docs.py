from drf_yasg import openapi
from drf_yasg.inspectors.field import get_basic_type_info
from testapp.api import ZaakSerializer


def test_type_info():
    field = ZaakSerializer().fields["zaaktype"]

    type_info = get_basic_type_info(field)

    assert type_info == {
        "type": openapi.TYPE_STRING,
        "format": openapi.FORMAT_URI,
        "min_length": 1,
    }
