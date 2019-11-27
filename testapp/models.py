from django.db import models

from django_loose_fk.fields import FkOrURLField


class ZaakType(models.Model):
    name = models.CharField("name", max_length=50)

    class Meta:
        verbose_name = "zaaktype"
        verbose_name_plural = "zaaktypen"

    def __str__(self):
        return self.name


class Zaak(models.Model):
    name = models.CharField("name", max_length=50)
    _zaaktype = models.ForeignKey(
        "ZaakType", null=True, blank=True, on_delete=models.PROTECT
    )
    extern_zaaktype = models.URLField(blank=True)
    zaaktype = FkOrURLField(fk_field="_zaaktype", url_field="extern_zaaktype")

    class Meta:
        verbose_name = "zaak"
        verbose_name_plural = "zaken"

    def __str__(self):
        return self.name


class ZaakObject(models.Model):
    name = models.CharField("name", max_length=50)
    _zaak = models.ForeignKey("Zaak", null=True, blank=True, on_delete=models.PROTECT)
    extern_zaak = models.URLField(blank=True)
    zaak = FkOrURLField(fk_field="_zaak", url_field="extern_zaak")


class DummyModel(models.Model):
    _zaaktype1 = models.ForeignKey(
        "ZaakType", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    extern_zaaktype1 = models.URLField(blank=True)
    zaaktype1 = FkOrURLField(fk_field="_zaaktype1", url_field="extern_zaaktype1")

    _zaaktype2 = models.ForeignKey(
        "ZaakType", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    extern_zaaktype2 = models.URLField(blank=True)
    zaaktype2 = FkOrURLField(
        fk_field="_zaaktype2", url_field="extern_zaaktype2", blank=True, null=True
    )


# m2m setups


class TypeA(models.Model):
    name = models.CharField("name", max_length=50)


class TypeB(models.Model):
    name = models.CharField("name", max_length=50)
    a_types = models.ManyToManyField("TypeA", blank=True)


class B(models.Model):
    local_type = models.ForeignKey(
        "TypeB", null=True, blank=True, on_delete=models.CASCADE
    )
    remote_type = models.URLField(blank=True)
    type = FkOrURLField("local_type", "remote_type", blank=True)


class C(models.Model):
    local_b = models.ForeignKey("B", on_delete=models.CASCADE, blank=True, null=True)
    remote_b = models.URLField(blank=True)
    b = FkOrURLField("local_b", "remote_b")
