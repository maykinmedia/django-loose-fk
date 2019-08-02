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
