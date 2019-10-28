from django.test import override_settings

import pytest
from django_filters.rest_framework.filterset import FilterSet
from rest_framework.reverse import reverse
from testapp.api import ZaakFilterSet, ZaakViewSet
from testapp.models import Zaak, ZaakType

from django_loose_fk.filters import FkOrUrlFieldFilter

pytestmark = pytest.mark.django_db()


class ZaakFilter(FilterSet):
    zaaktype = FkOrUrlFieldFilter(queryset=ZaakType.objects.all(), instance_path="name")

    class Meta:
        model = Zaak
        fields = ("zaaktype",)


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
