"""
Test that it's possibly to handle remote/local objects transparently.
"""
import pytest
import requests_mock
from testapp.models import B, TypeA, TypeB, Zaak, ZaakType

pytestmark = pytest.mark.django_db


def test_create_local_fk():
    zt = ZaakType.objects.create(name="test")

    zaak = Zaak.objects.create(name="test", zaaktype=zt)

    assert zaak.pk is not None
    assert zaak._zaaktype == zt


def test_create_remote_url():
    zaak = Zaak.objects.create(name="test", zaaktype="https://example.com/zt/123")

    assert zaak.pk is not None
    assert zaak.extern_zaaktype == "https://example.com/zt/123"


def test_accessor_local_fk():
    zt = ZaakType.objects.create(name="test")

    zaak = Zaak.objects.create(name="test", zaaktype=zt)

    assert isinstance(zaak.zaaktype, ZaakType)
    assert zaak.zaaktype == zt


def test_accessor_remote_url():
    """
    Test that accessing the zaaktype from remote imports the remote
    and creates a local instance.
    """
    zaak = Zaak.objects.create(name="test", zaaktype="https://example.com/zt/123")

    with requests_mock.Mocker() as m:
        m.get(
            "https://example.com/zt/123",
            json={"url": "https://example.com/zt/123", "name": "remote"},
        )
        zaaktype = zaak.zaaktype

    assert isinstance(zaaktype, ZaakType)
    assert zaaktype.pk is None
    assert zaaktype.name == "remote"

    with pytest.raises(RuntimeError):
        zaaktype.save()


def test_create_with_local_m2m():
    type_a = TypeA.objects.create(name="a")
    type_b = TypeB.objects.create(name="b")
    type_b.a_types.set([type_a])

    b = B.objects.create(type=type_b)

    assert b.type.pk is not None
    assert type_a in b.type.a_types.all()
