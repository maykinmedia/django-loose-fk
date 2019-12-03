from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework import routers, serializers, viewsets

from django_loose_fk.filters import FkOrUrlFieldFilter

from .models import Zaak, ZaakObject, ZaakType

# Serializers


class ZaakTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakType
        fields = ("url", "name")


class ZaakSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Zaak
        fields = ("url", "zaaktype", "name")


class ZaakObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakObject
        fields = ("url", "zaak", "name")


# Filters


class ZaakFilterSet(FilterSet):
    class Meta:
        model = Zaak
        fields = ("zaaktype",)


class ZaakObjectFilterset(FilterSet):
    zaak = FkOrUrlFieldFilter(queryset=ZaakObject.objects.all())

    class Meta:
        model = ZaakObject
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


# URL routing

router = routers.DefaultRouter()
router.register("zaaktypes", ZaakTypeViewSet)
router.register("zaken", ZaakViewSet)
router.register("zaakobjecten", ZaakObjectViewSet)
