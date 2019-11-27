from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from django.core import checks
from django.db import models
from django.db.models import Field
from django.db.models.base import ModelBase, Options

from .loaders import BaseLoader, default_loader
from .virtual_models import ProxyMixin

InstanceOrUrl = Union[models.Model, str]


@dataclass
class FkOrURLField(models.Field):
    fk_field: str
    url_field: str
    verbose_name: Optional[str] = None
    blank: bool = False
    null: bool = False
    help_text: Optional[str] = ""

    loader: BaseLoader = default_loader

    name = None

    _unique = False  # TODO: support this

    # attributes that django.db.models.fields.Field normally sets
    creation_counter = 0

    remote_field = None
    is_relation = False
    primary_key = False
    auto_created = False
    concrete = False
    column = None

    many_to_many = None
    default = models.NOT_PROVIDED
    db_index = False
    db_column = None
    serialize = True
    unique_for_date = None
    unique_for_month = None
    unique_for_year = None
    _validators = ()
    editable = True
    choices = ()

    def __post_init__(self):
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def __lt__(self, other):
        # This is needed because bisect does not take a comparison function.
        if isinstance(other, Field):
            return self.creation_counter < other.creation_counter
        return NotImplemented

    def __hash__(self):
        return hash(self.creation_counter)

    def contribute_to_class(
        self, cls: ModelBase, name: str, private_only: bool = False
    ):
        """
        Register the field with the model class.
        """
        self.name = name
        self.model = cls

        cls._meta.add_field(self)
        self._add_check_constraint(cls._meta)

        # install the descriptor
        setattr(cls, self.name, FkOrURLDescriptor(self))

    def _add_check_constraint(
        self, options: Options, name: str = "{fk_field}_or_{url_field}_filled"
    ) -> None:
        """
        Create the DB constraints and add them if they're not present yet.
        """
        # if the field can be null/empty, we don't need the constraint to
        # guarantee that exactly one of both fields is filled.
        if self.null:
            return

        # URL field is empty if empty string or None
        empty_url_field = models.Q(**{self.url_field: ""})
        empty_fk_field = models.Q(**{f"{self.fk_field}__isnull": True})

        fk_filled = ~empty_fk_field & empty_url_field
        url_filled = empty_fk_field & ~empty_url_field

        # one of both MUST be filled and they cannot be filled both at the
        # same time
        check = fk_filled | url_filled

        # check if the same constraint already exists or not - if it does, we
        # don't need to add it
        if any(
            (
                constraint.check == check
                for constraint in options.constraints
                if hasattr(constraint, "check")
            )
        ):
            return

        name = name.format(fk_field=self.fk_field, url_field=self.url_field)
        options.constraints.append(models.CheckConstraint(check=check, name=name))

    @property
    def _fk_field(self) -> models.ForeignKey:
        # get the actual fields - uses private API because the app registry isn't
        # ready yet
        # TODO: maybe it is now?
        _fields = {field.name: field for field in self.model._meta.fields}
        return _fields[self.fk_field]

    @property
    def _url_field(self) -> models.URLField:
        # get the actual fields - uses private API because the app registry isn't
        # ready yet
        # TODO: maybe it is now?
        _fields = {field.name: field for field in self.model._meta.fields}
        return _fields[self.url_field]

    def check(self, **kwargs) -> List[checks.Error]:
        errors = []
        if not isinstance(self._fk_field, models.ForeignKey):
            errors.append(
                checks.Error(
                    "The field passed to 'fk_field' should be a ForeignKey",
                    obj=self,
                    id="fk_or_url_field.E001",
                )
            )

        if not isinstance(self._url_field, models.URLField):
            errors.append(
                checks.Error(
                    "The field passed to 'url_field' should be a URLField",
                    obj=self,
                    id="fk_or_url_field.E002",
                )
            )
        elif self._url_field.null:
            errors.append(
                checks.Error(
                    f"The URLField '{self.url_field}' may not be nullable",
                    obj=self,
                    id="fk_or_url_field.E003",
                )
            )

        return errors

    @property
    def attname(self) -> str:
        return self.name

    def get_attname_column(self) -> Tuple[str, None]:
        return self.attname, None

    def clone(self):
        """
        Uses deconstruct() to clone a new copy of this Field.
        Will not preserve any class attachments/attribute names.
        """
        name, path, args, kwargs = self.deconstruct()
        return self.__class__(*args, **kwargs)

    def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)
        keywords = {
            "fk_field": self.fk_field,
            "url_field": self.url_field,
            "blank": self.blank,
            "null": self.null,
        }
        return (self.name, path, [], keywords)

    @property
    def max_length(self) -> Union[None, int]:
        return self._url_field.max_length


@dataclass
class FkOrURLDescriptor:
    field: FkOrURLField

    @property
    def fk_field_name(self) -> str:
        return self.field._fk_field.name

    @property
    def url_field_name(self) -> str:
        return self.field._url_field.name

    def __get__(self, instance, cls=None):
        """
        Get the related instance through the forward relation.
        """
        if instance is None:
            return self

        # if the value is select_related, this will hit that cache
        pk_value = getattr(instance, self.field._fk_field.attname)
        if pk_value is not None:
            fk_value = getattr(instance, self.fk_field_name)
            if fk_value is not None:
                return fk_value

        url_value = getattr(instance, self.url_field_name)
        if not url_value:
            if not self.field.null:
                raise ValueError("No FK value and no URL value, this is not allowed!")
            return None

        remote_model = self.field._fk_field.related_model
        remote_loader = self.field.loader
        return remote_loader.load(url=url_value, model=remote_model)

    def __set__(self, instance: models.Model, value: Optional[InstanceOrUrl]):
        """
        Set the related instance through the forward relation.

        Delegate the set action to the appropriate field.
        """
        if value is None and not self.field.null:
            raise ValueError(
                "A 'None'-value is not allowed. Make the field "
                "nullable if empty values should be supported."
            )

        if isinstance(value, ProxyMixin):
            value = value._loose_fk_data["url"]

        if isinstance(value, models.Model):
            field_name = self.fk_field_name
        elif isinstance(value, str):
            field_name = self.url_field_name
        elif value is None:
            setattr(instance, self.url_field_name, "")
            setattr(instance, self.fk_field_name, None)
            return
        else:
            raise TypeError(f"value is of type {type(value)}, which is not supported.")
        setattr(instance, field_name, value)
