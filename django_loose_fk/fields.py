from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from django.core import checks
from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models import Field
from django.db.models.base import ModelBase, Options
from django.db.models.fields.related_lookups import RelatedIn
from django.db.models.lookups import In as _In

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

    # attributes that django.db.models.fields.Field normally sets
    creation_counter = 0

    remote_field = None
    is_relation = False
    primary_key = False
    auto_created = False
    concrete = False
    column = None

    many_to_many = None
    null = False
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
        keywords = {"fk_field": self.fk_field, "url_field": self.url_field}
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
            raise ValueError("No FK value and no URL value, this is not allowed!")

        remote_model = self.field._fk_field.related_model
        remote_loader = self.field.loader
        return remote_loader.load(url=url_value, model=remote_model)

    def __set__(self, instance: models.Model, value: InstanceOrUrl):
        """
        Set the related instance through the forward relation.

        Delegate the set action to the appropriate field.
        """
        if isinstance(value, ProxyMixin):
            value = value._loose_fk_data["url"]

        if isinstance(value, models.Model):
            field_name = self.fk_field_name
        elif isinstance(value, str):
            field_name = self.url_field_name
        else:
            raise TypeError(f"value is of type {type(value)}, which is not supported.")
        setattr(instance, field_name, value)


def get_normalized_value(value) -> tuple:
    if isinstance(value, ProxyMixin):
        return (value._loose_fk_data["url"],)

    if isinstance(value, models.Model):
        return (value.pk,)

    if not isinstance(value, tuple):
        return (value,)
    return value


class In(RelatedIn):
    """
    Split the IN query into two IN queries, per datatype.

    Creates an IN query for the url field values, and an IN query for the FK
    field values, joined together by an OR.
    """

    lookup_name = "in"

    def process_lhs(self, compiler, connection, lhs=None):
        target = self.lhs.target
        db_table = target.model._meta.db_table

        url_lhs = target._url_field.get_col(db_table)
        fk_lhs = target._fk_field.get_col(db_table)

        url_lhs_sql, url_params = super().process_lhs(compiler, connection, lhs=url_lhs)
        fk_lhs_sql, fk_params = super().process_lhs(compiler, connection, lhs=fk_lhs)

        return (url_lhs_sql, url_params, fk_lhs_sql, fk_params)

    def process_remote_rhs(self) -> List[str]:
        """
        Extract URLs to filter on for remote RHS.

        self.rhs is normalized here already.
        """
        return [obj for obj in self.rhs if isinstance(obj, str)]

    def process_rhs(self, compiler, connection):
        if self.rhs_is_direct_value():
            remote_rhs = self.process_remote_rhs()

            if remote_rhs:
                target = self.lhs.target
                db_table = target.model._meta.db_table
                url_lhs = target._url_field.get_col(db_table)
                _remote_lookup = _In(url_lhs, remote_rhs)
                url_rhs_sql, url_rhs_params = _remote_lookup.process_rhs(
                    compiler, connection
                )
            else:
                url_rhs_sql, url_rhs_params = None, ()

            # filter out the remote objects
            self.rhs = [obj for obj in self.rhs if obj not in remote_rhs]
            if not self.rhs:
                fk_rhs_sql, fk_rhs_params = None, ()
            else:
                fk_rhs_sql, fk_rhs_params = super().process_rhs(compiler, connection)
        else:
            # we're dealing with something that can be expressed as SQL -> it's local only!
            url_rhs_sql, url_rhs_params = None, ()
            fk_rhs_sql, fk_rhs_params = super().process_rhs(compiler, connection)

        return url_rhs_sql, url_rhs_params, fk_rhs_sql, fk_rhs_params

    def get_prep_lookup(self):
        if self.rhs_is_direct_value():
            # If we get here, we are dealing with single-column relations.
            self.rhs = [get_normalized_value(val)[0] for val in self.rhs]
        return super().get_prep_lookup()

    def as_sql(self, compiler, connection):
        # TODO: support connection.ops.max_in_list_size()
        url_lhs_sql, url_params, fk_lhs_sql, fk_params = self.process_lhs(
            compiler, connection
        )
        url_rhs_sql, url_rhs_params, fk_rhs_sql, fk_rhs_params = self.process_rhs(
            compiler, connection
        )

        if not fk_rhs_sql and not url_rhs_sql:
            raise EmptyResultSet()

        if fk_rhs_sql:
            fk_rhs_sql = self.get_rhs_op(connection, fk_rhs_sql)
            fk_sql = (
                "%s %s" % (fk_lhs_sql, fk_rhs_sql),
                tuple(fk_params) + fk_rhs_params,
            )

        if url_rhs_sql:
            url_rhs_sql = self.get_rhs_op(connection, url_rhs_sql)
            url_sql = (
                "%s %s" % (url_lhs_sql, url_rhs_sql),
                tuple(url_params) + url_rhs_params,
            )

        if not fk_rhs_sql:
            return url_sql

        if not url_rhs_sql:
            return fk_sql

        params = url_sql[1] + fk_sql[1]
        sql = "(%s OR %s)" % (url_sql[0], fk_sql[0])

        return sql, params


FkOrURLField.register_lookup(In)
