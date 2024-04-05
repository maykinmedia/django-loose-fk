from django.db import models
from django.db.models.constraints import BaseConstraint
from django.db.utils import DEFAULT_DB_ALIAS


class FkOrURLFieldConstraint(BaseConstraint):
    """
    Wrap around models.CheckConstraint based on the field name passed in.
    """

    _check_name = "{prefix}{fk_field}_or_{url_field}_filled"

    def __init__(
        self, fk_field: str, url_field: str, app_label: str = "", model_name: str = ""
    ):
        self.app_label = app_label
        self.model_name = model_name
        self.fk_field = fk_field
        self.url_field = url_field
        prefix = f"{app_label}_{model_name}_" if app_label and model_name else ""
        name = self._check_name.format(
            fk_field=fk_field, url_field=url_field, prefix=prefix
        )
        super().__init__(name)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        del kwargs["name"]
        kwargs.update(
            {
                "app_label": self.app_label,
                "model_name": self.model_name,
                "fk_field": self.fk_field,
                "url_field": self.url_field,
            }
        )
        return (path, args, kwargs)

    def _get_check_constraint(self, model, schema_editor=None):
        """
        Return the underlying check constraint generated.
        """
        if not hasattr(self, "_check_constraint"):
            # URL field is empty if empty string or None
            empty_url_field = models.Q(**{self.url_field: ""})
            empty_fk_field = models.Q(**{f"{self.fk_field}__isnull": True})

            fk_filled = ~empty_fk_field & empty_url_field
            url_filled = empty_fk_field & ~empty_url_field

            # one of both MUST be filled and they cannot be filled both at the
            # same time
            check = fk_filled | url_filled
            self._check_constraint = models.CheckConstraint(check=check, name=self.name)

        return self._check_constraint

    def constraint_sql(self, model, schema_editor):
        check_constraint = self._get_check_constraint(model, schema_editor)
        return check_constraint.constraint_sql(model, schema_editor)

    def create_sql(self, model, schema_editor):
        check_constraint = self._get_check_constraint(model, schema_editor)
        return check_constraint.create_sql(model, schema_editor)

    def remove_sql(self, model, schema_editor):
        check_constraint = self._get_check_constraint(model, schema_editor)
        return check_constraint.remove_sql(model, schema_editor)

    def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        check_constraint = self._get_check_constraint(model)
        return check_constraint.validate(model, instance, exclude, using)

    def __repr__(self):
        return "<%s: field=%r>" % (self.__class__.__name__, self.name)

    def __eq__(self, other):
        if isinstance(other, FkOrURLFieldConstraint):
            return self.name == other.name
        return super().__eq__(other)
