from django.db.utils import IntegrityError

import pytest
from testapp.models import Zaak, ZaakType

pytestmark = pytest.mark.django_db


def test_both_url_and_fk():
    zt = ZaakType.objects.create(name="test")

    with pytest.raises(IntegrityError):
        Zaak.objects.create(_zaaktype=zt, extern_zaaktype="https://example.com")


def test_neither_url_or_fk():
    with pytest.raises(IntegrityError):
        Zaak.objects.create(_zaaktype=None, extern_zaaktype="")


def test_only_url():
    zaak = Zaak.objects.create(extern_zaaktype="https://example.com")

    assert zaak.pk is not None


def test_only_fk():
    zt = ZaakType.objects.create(name="test")

    zaak = Zaak.objects.create(_zaaktype=zt)

    assert zaak.pk is not None
