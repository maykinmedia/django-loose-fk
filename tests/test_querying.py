"""
Test the ORM queries against the virtual field.
"""
import pytest
import requests_mock
from testapp.models import Zaak, ZaakType

pytestmark = pytest.mark.django_db


def test_in_lookup_local_fk():
    local_zaaktype = ZaakType.objects.create(name="local")
    zaak1 = Zaak.objects.create(zaaktype=local_zaaktype)
    Zaak.objects.create(zaaktype="https://example.com/zt/123")

    qs = Zaak.objects.filter(zaaktype__in=[local_zaaktype])

    assert list(qs) == [zaak1]


def test_in_lookup_with_queryset_local_fk():
    local_zaaktype = ZaakType.objects.create(name="local")
    zaak1 = Zaak.objects.create(zaaktype=local_zaaktype)
    Zaak.objects.create(zaaktype="https://example.com/zt/123")

    qs = Zaak.objects.filter(zaaktype__in=ZaakType.objects.all())

    assert list(qs) == [zaak1]


def test_in_lookup_with_url_value():
    local_zaaktype = ZaakType.objects.create(name="local")
    Zaak.objects.create(zaaktype=local_zaaktype)
    zaak2 = Zaak.objects.create(zaaktype="https://example.com/zt/123")

    qs = Zaak.objects.filter(zaaktype__in=["https://example.com/zt/123"])

    assert list(qs) == [zaak2]


def test_in_lookup_with_virtual_model():
    local_zaaktype = ZaakType.objects.create(name="local")
    Zaak.objects.create(zaaktype=local_zaaktype)
    zaak2 = Zaak.objects.create(zaaktype="https://example.com/zt/123")
    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/zt/123",
            json={"url": "https://example.com/zt/123", "name": "remote"},
        )
        zaaktype = zaak2.zaaktype

    qs = Zaak.objects.filter(zaaktype__in=[zaaktype])

    assert list(qs) == [zaak2]