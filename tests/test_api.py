"""
Test the API interface to handle local/remote references.
"""
import pytest
import requests_mock
from rest_framework.reverse import reverse
from testapp.models import Zaak, ZaakType

pytestmark = pytest.mark.django_db()


def test_read_fk_gives_local_url(api_client):
    zaaktype = ZaakType.objects.create(name="test")
    zaak = Zaak.objects.create(name="test", zaaktype=zaaktype)
    url = reverse("zaak-detail", kwargs={"pk": zaak.pk})
    zaaktype_url = reverse("zaaktype-detail", kwargs={"pk": zaaktype.pk})

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        "url": f"http://testserver{url}",
        "zaaktype": f"http://testserver{zaaktype_url}",
        "name": "test",
    }


def test_read_remote_url_gives_remote_url(api_client):
    zaak = Zaak.objects.create(
        name="test", zaaktype="https://example.com/zaaktypen/123"
    )
    url = reverse("zaak-detail", kwargs={"pk": zaak.pk})

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        "url": f"http://testserver{url}",
        "zaaktype": "https://example.com/zaaktypen/123",
        "name": "test",
    }


def test_write_local_url(api_client):
    url = reverse("zaak-list")
    zaaktype = ZaakType.objects.create(name="test")
    zaaktype_url = reverse("zaaktype-detail", kwargs={"pk": zaaktype.pk})

    data = {"name": "test", "zaaktype": f"http://testserver{zaaktype_url}"}

    response = api_client.post(url, data)

    assert response.status_code == 201
    zaak = Zaak.objects.get()
    assert zaak.zaaktype == zaaktype


def test_write_remote_url(api_client):
    url = reverse("zaak-list")
    zaaktype_url = "https://example.com/zaaktypen/123"

    with requests_mock.Mocker() as m:
        m.get(zaaktype_url, json={"url": zaaktype_url, "name": "test"})

        response = api_client.post(url, {"name": "test", "zaaktype": zaaktype_url})

        assert response.status_code == 201
        zaak = Zaak.objects.get()
        assert zaak.extern_zaaktype == zaaktype_url
        assert zaak.zaaktype.pk is None


def test_write_invalid_local_url(api_client):
    url = reverse("zaak-list")
    zaaktype_url = reverse("zaaktype-detail", kwargs={"pk": 0})

    data = {"name": "test", "zaaktype": f"http://testserver{zaaktype_url}"}

    response = api_client.post(url, data)

    assert response.status_code == 400
    assert "zaaktype" in response.data
    assert response.data["zaaktype"][0].code == "does_not_exist"


def test_filter_zaaktype_remote_url(api_client):
    url = reverse("zaak-list")
    zaak = Zaak.objects.create(
        name="test", zaaktype="https://example.com/zaaktypen/123"
    )
    zaak_url = reverse("zaak-detail", kwargs={"pk": zaak.pk})
    Zaak.objects.create(name="test", zaaktype="https://example.com/zaaktypen/456")

    response = api_client.get(url, {"zaaktype": "https://example.com/zaaktypen/123"})

    assert len(response.data) == 1
    assert response.data[0]["url"] == f"http://testserver{zaak_url}"


def test_filter_zaaktype_local_fk(api_client):
    url = reverse("zaak-list")
    zaaktype1 = ZaakType.objects.create(name="foo")
    zaaktype_path = reverse("zaaktype-detail", kwargs={"pk": zaaktype1.pk})
    zaaktype2 = ZaakType.objects.create(name="bar")
    zaak = Zaak.objects.create(name="test", zaaktype=zaaktype1)
    Zaak.objects.create(name="test", zaaktype=zaaktype2)
    zaak_url = reverse("zaak-detail", kwargs={"pk": zaak.pk})

    response = api_client.get(
        url,
        {"zaaktype": f"http://testserver.com{zaaktype_path}"},
        HTTP_HOST="testserver.com",
    )

    assert len(response.data) == 1
    assert response.data[0]["url"] == f"http://testserver.com{zaak_url}"
