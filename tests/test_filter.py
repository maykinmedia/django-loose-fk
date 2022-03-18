from django.test import override_settings

import pytest
from django_filters.rest_framework.filterset import FilterSet
from rest_framework.reverse import reverse

from testapp.api import ZaakFilterSet, ZaakViewSet
from testapp.models import Zaak, ZaakType

pytestmark = pytest.mark.django_db()


class ZaakFilter(FilterSet):
    class Meta:
        model = Zaak
        fields = {
            "zaaktype": ["exact", "in"],
        }


@override_settings(ALLOWED_HOSTS=["testserver.com"])
def test_fk_or_url_field_filter_with_instance_path(api_client):
    ZaakViewSet.filterset_class = ZaakFilter

    zaaktype = ZaakType.objects.create(name=1)
    zaaktype_uri = reverse("zaaktype-detail", kwargs={"pk": zaaktype.pk})
    zaaktype_url = f"http://testserver.com{zaaktype_uri}"

    zaak = Zaak.objects.create(name="bla", zaaktype=zaaktype)
    zaak_uri = reverse("zaak-detail", kwargs={"pk": zaak.pk})
    zaak_url = f"http://testserver.com{zaak_uri}"

    url = reverse("zaak-list")

    # Filtering on Zaaktype should first resolve the URL to the correct
    # ZaakType in the database, then it will use the instance_path to find
    # the attribute that we're interested in. which is `name` in this case
    response = api_client.get(
        url, {"zaaktype": zaaktype_url}, HTTP_HOST="testserver.com"
    )

    ZaakViewSet.filterset_class = ZaakFilterSet

    assert response.status_code == 200
    assert response.data == [{"url": zaak_url, "zaaktype": zaaktype_url, "name": "bla"}]


@override_settings(ALLOWED_HOSTS=["testserver.com"])
def test_fk_or_url_field_filter_with_list(api_client):
    ZaakViewSet.filterset_class = ZaakFilter

    zaaktype1 = ZaakType.objects.create(name=1)
    zaaktype1_uri = reverse("zaaktype-detail", kwargs={"pk": zaaktype1.pk})
    zaaktype1_url = f"http://testserver.com{zaaktype1_uri}"
    zaaktype2 = ZaakType.objects.create(name=2)
    zaaktype2_uri = reverse("zaaktype-detail", kwargs={"pk": zaaktype2.pk})
    zaaktype2_url = f"http://testserver.com{zaaktype2_uri}"
    zaaktype3 = ZaakType.objects.create(name=3)

    zaak1 = Zaak.objects.create(name="bla1", zaaktype=zaaktype1)
    zaak1_uri = reverse("zaak-detail", kwargs={"pk": zaak1.pk})
    zaak1_url = f"http://testserver.com{zaak1_uri}"
    zaak2 = Zaak.objects.create(name="bla2", zaaktype=zaaktype2)
    zaak2_uri = reverse("zaak-detail", kwargs={"pk": zaak2.pk})
    zaak2_url = f"http://testserver.com{zaak2_uri}"
    Zaak.objects.create(name="bla3", zaaktype=zaaktype3)

    url = reverse("zaak-list")

    response = api_client.get(
        url,
        {"zaaktype__in": f"{zaaktype1_url},{zaaktype2_url}"},
        HTTP_HOST="testserver.com",
    )

    ZaakViewSet.filterset_class = ZaakFilterSet

    assert response.status_code == 200
    assert len(response.data) == 2
    assert {
        "url": zaak1_url,
        "zaaktype": zaaktype1_url,
        "name": "bla1",
    } in response.data
    assert {
        "url": zaak2_url,
        "zaaktype": zaaktype2_url,
        "name": "bla2",
    } in response.data


@override_settings(ALLOWED_HOSTS=["testserver.com"])
def test_filter_with_remote_url(api_client):
    ZaakViewSet.filterset_class = ZaakFilter

    Zaak.objects.create(name="test1", zaaktype="https://example.com/zt/123")
    Zaak.objects.create(name="test2", zaaktype="https://example.com/zt/456")

    response = api_client.get(
        reverse("zaak-list"),
        {"zaaktype": "https://example.com/zt/456"},
        HTTP_HOST="testserver.com",
    )

    ZaakViewSet.filterset_class = ZaakFilterSet

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "test2"
