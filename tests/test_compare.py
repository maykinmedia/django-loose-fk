"""
Test the API interface to handle comparing of loose-fk urls
"""
import pytest
import requests_mock
from testapp.models import Zaak, ZaakType

pytestmark = pytest.mark.django_db()


def test_compare_local_urls(api_client):
    zaaktype = ZaakType.objects.create(name="zaaktype")
    zaak1 = Zaak.objects.create(zaaktype=zaaktype, name="zaak1")
    zaak2 = Zaak.objects.create(zaaktype=zaaktype, name="zaak2")

    assert zaak1.zaaktype == zaak2.zaaktype


def test_compare_remote_urls(api_client):
    zaaktype = "https://example.com/zaaktypen/123"
    zaak1 = Zaak.objects.create(zaaktype=zaaktype, name="zaak1")
    zaak2 = Zaak.objects.create(zaaktype=zaaktype, name="zaak2")

    with requests_mock.Mocker() as m:
        m.get(zaaktype, json={"url": zaaktype, "name": "zaaktype"})

        assert zaak1.zaaktype == zaak2.zaaktype
