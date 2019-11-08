import pytest
import requests_mock
from testapp.models import Zaak, ZaakType

from django_loose_fk.loaders import FetchError, FetchJsonError, default_loader


@pytest.mark.django_db
def test_pluggable_loader(settings):
    settings.DEFAULT_LOOSE_FK_LOADER = "testapp.loaders.DummyLoader"

    zaak = Zaak.objects.create(zaaktype="https://example.com/dummy")

    assert zaak.zaaktype.name == "dummy"


@pytest.mark.parametrize("status_code", [401, 402, 403, 404, 405, 500])
def test_failed_fetch(status_code):
    with requests_mock.Mocker() as m:
        m.get("https://example.com/dummy", status_code=status_code)

        with pytest.raises(FetchError):
            default_loader.load("https://example.com/dummy", ZaakType)


def test_failed_not_json():
    with requests_mock.Mocker() as m:
        m.get("https://example.com", text="some text")

        with pytest.raises(FetchJsonError):
            default_loader.load("https://example.com", ZaakType)
