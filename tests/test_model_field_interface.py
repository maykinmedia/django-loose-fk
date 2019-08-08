"""
Test that it's possibly to handle remote/local objects transparently.
"""
import pytest
import requests_mock
from testapp.models import B, C, TypeA, TypeB, Zaak, ZaakType

from django_loose_fk.loaders import BaseLoader

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


class TypeLoader(BaseLoader):
    @staticmethod
    def fetch_object(url: str) -> dict:
        data = {"url": url}

        if url.endswith("b-instance"):
            data.update(type="https://example.com/type-b")
        elif url.endswith("a"):
            data.update(name="a")
        elif url.endswith("b"):
            data.update(name="b", a_types=["https://example.com/type-a"])
        else:
            raise ValueError("Unknown URL")

        return data


def test_create_with_remote_m2m(settings):
    settings.DEFAULT_LOOSE_FK_LOADER = "tests.test_model_field_interface.TypeLoader"

    b = B.objects.create(type="https://example.com/type-b")

    assert b.type.name == "b"
    a_type = b.type.a_types.get()
    assert a_type.name == "a"


def test_chained_remotes_fk(settings):
    settings.DEFAULT_LOOSE_FK_LOADER = "tests.test_model_field_interface.TypeLoader"

    c = C.objects.create(b="https://example.com/b-instance")

    assert c.b.type.name == "b"
