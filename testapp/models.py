from django.db import models

from django_loose_fk.fields import FkOrURLField


class ZaakType(models.Model):
    name = models.CharField("name", max_length=50)

    class Meta:
        verbose_name = "zaaktype"
        verbose_name_plural = "zaaktypen"

    def __str__(self):
        return self.name


fk_filled = models.Q(_zaaktype__isnull=False) & models.Q(extern_zaaktype="")
url_filled = models.Q(_zaaktype__isnull=True) & ~models.Q(extern_zaaktype="")


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
        constraints = [
            models.CheckConstraint(
                check=fk_filled | url_filled, name="fk_or_url_filled"
            )
        ]

    def __str__(self):
        return self.name
