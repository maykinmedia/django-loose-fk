from rest_framework.serializers import ModelSerializer
from testapp.models import DummyModel


class Serializer(ModelSerializer):
    class Meta:
        model = DummyModel
        fields = ("zaaktype1", "zaaktype2")


def test_not_null_not_blank():
    # model field has blank=False and null=False as defaults
    field = Serializer().fields["zaaktype1"]

    assert field.required is True
    assert field.allow_null is False


def test_blankable_nullable_field():
    # model field has blank=True and null=True
    field = Serializer().fields["zaaktype2"]

    assert field.required is False
    assert field.allow_null is True
