"""
Test the API interface to handle chained local/remote references.
"""
import pytest
import requests_mock
from rest_framework.reverse import reverse
from testapp.models import ZaakObject, ZaakType

pytestmark = pytest.mark.django_db()


def test_get_local_fk_after_remote_url(api_client):
    zaaktype = ZaakType.objects.create(name="test")
    zaaktype_url = reverse("zaaktype-detail", kwargs={"pk": zaaktype.pk})
    zaak_url = "https://example.com/zaaktypen/123"

    url = reverse("zaakobject-list")

    with requests_mock.Mocker() as m:
        m.get(
            zaak_url,
            json={
                "url": zaak_url,
                "name": "test",
                "zaaktype": f"http://testserver.com{zaaktype_url}",
            },
        )

        response = api_client.post(
            url, {"name": "test", "zaak": zaak_url}, HTTP_HOST="testserver.com"
        )

        assert response.status_code == 201
        zaakobject = ZaakObject.objects.get()

        assert zaakobject.zaak.zaaktype == zaaktype
