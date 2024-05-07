from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework import routers, serializers, viewsets

from django_loose_fk.filters import FkOrUrlFieldFilter

from .models import Zaak, ZaakObject, ZaakObjectFk, ZaakType

# Serializers


class ZaakTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakType
        fields = ("url", "name")


class ZaakSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Zaak
        fields = ("url", "zaaktype", "name")
        extra_kwargs = {"zaaktype": {"max_length": 1000}}


class ZaakObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakObject
        fields = ("url", "zaak", "name")


class ZaakObjectFkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakObjectFk
        fields = ("zaak_object", "name")


# Filters


class ZaakFilterSet(FilterSet):
    class Meta:
        model = Zaak
        fields = {
            "zaaktype": ["exact", "in"],
        }


class ZaakObjectFilterset(FilterSet):
    zaak = FkOrUrlFieldFilter(queryset=ZaakObject.objects.all())

    class Meta:
        model = ZaakObject
        fields = ("zaak",)


class ZaakObjectFkFilterset(FilterSet):
    zaak = FkOrUrlFieldFilter(
        queryset=ZaakObjectFk.objects.all(),
        field_name="zaak_object__zaak",
    )

    class Meta:
        model = ZaakObjectFk
        fields = ("zaak",)


# Viewsets


class NoAuthMixin:
    def perform_authentication(self, request):
        pass


class ZaakTypeViewSet(NoAuthMixin, viewsets.ModelViewSet):
    queryset = ZaakType.objects.all()
    serializer_class = ZaakTypeSerializer


class ZaakViewSet(NoAuthMixin, viewsets.ModelViewSet):
    queryset = Zaak.objects.all()
    serializer_class = ZaakSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ZaakFilterSet


class ZaakObjectViewSet(NoAuthMixin, viewsets.ModelViewSet):
    queryset = ZaakObject.objects.all()
    serializer_class = ZaakObjectSerializer
    filterset_class = ZaakObjectFilterset


class ZaakObjectFkViewSet(NoAuthMixin, viewsets.ModelViewSet):
    queryset = ZaakObjectFk.objects.all()
    filter_backends = (DjangoFilterBackend,)
    serializer_class = ZaakObjectFkSerializer
    filterset_class = ZaakObjectFkFilterset


# URL routing

router = routers.DefaultRouter()
router.register("zaaktypes", ZaakTypeViewSet)
router.register("zaken", ZaakViewSet)
router.register("zaakobjecten", ZaakObjectViewSet)
router.register("zaakobjectfk", ZaakObjectFkViewSet)
