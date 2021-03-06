# Generated by Django 2.2.7 on 2019-11-27 05:36

import django.db.models.deletion
from django.db import migrations, models

import django_loose_fk.fields


class Migration(migrations.Migration):

    dependencies = [("testapp", "0003_auto_20190808_1647")]

    operations = [
        migrations.CreateModel(
            name="ZaakObject",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="name")),
                ("extern_zaak", models.URLField(blank=True)),
                (
                    "_zaak",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="testapp.Zaak",
                    ),
                ),
                (
                    "zaak",
                    django_loose_fk.fields.FkOrURLField(
                        blank=False,
                        fk_field="_zaak",
                        null=False,
                        url_field="extern_zaak",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="zaakobject",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(_negated=True, _zaak__isnull=True), ("extern_zaak", "")
                    ),
                    models.Q(
                        ("_zaak__isnull", True), models.Q(_negated=True, extern_zaak="")
                    ),
                    _connector="OR",
                ),
                name="_zaak_or_extern_zaak_filled",
            ),
        ),
    ]
