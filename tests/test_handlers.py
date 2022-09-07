import pytest
import requests_mock

from testapp.models import ZaakObject


@pytest.mark.django_db
def test_pluggable_handlers(settings):
    settings.DEFAULT_LOOSE_FK_HANDLERS = "testapp.handlers.HANDLERS"

    zaak_url = "http://example.com/zaken/123"

    with requests_mock.Mocker() as m:
        m.get(zaak_url, json={"url": zaak_url, "name": "test zaak"})
        zaakobject = ZaakObject.objects.create(name="test zaak object", zaak=zaak_url)

        assert zaakobject.zaak._zaaktype == "dummy"
