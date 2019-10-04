from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework import routers, serializers, viewsets

from .models import Zaak, ZaakType

# Serializers


class ZaakTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ZaakType
        fields = ("url", "name")


class ZaakSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Zaak
        fields = ("url", "zaaktype", "name")


# Filters


class ZaakFilterSet(FilterSet):
    class Meta:
        model = Zaak
        fields = ("zaaktype",)


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


# URL routing

router = routers.DefaultRouter()
router.register("zaaktypes", ZaakTypeViewSet)
router.register("zaken", ZaakViewSet)
