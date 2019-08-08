import pytest
from testapp.models import Zaak


@pytest.mark.django_db
def test_pluggable_loader(settings):
    settings.DEFAULT_LOOSE_FK_LOADER = "testapp.loaders.DummyLoader"

    zaak = Zaak.objects.create(zaaktype="https://example.com/dummy")

    assert zaak.zaaktype.name == "dummy"
