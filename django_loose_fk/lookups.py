from typing import List, Tuple

from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models.fields.related_lookups import RelatedIn
from django.db.models.lookups import Exact as _Exact, In as _In

from .fields import FkOrURLField
from .virtual_models import ProxyMixin


def get_normalized_value(value) -> tuple:
    if isinstance(value, ProxyMixin):
        return (value._loose_fk_data["url"],)

    if isinstance(value, models.Model):
        return (value.pk,)

    if not isinstance(value, tuple):
        return (value,)
    return value


class FkOrURLFieldMixin:
    def _split_lhs(
        self, compiler, connection, lhs=None
    ) -> Tuple[str, tuple, str, tuple]:
        target = self.lhs.target
        db_table = target.model._meta.db_table

        url_lhs = target._url_field.get_col(db_table)
        fk_lhs = target._fk_field.get_col(db_table)

        url_lhs_sql, url_params = super().process_lhs(compiler, connection, lhs=url_lhs)
        fk_lhs_sql, fk_params = super().process_lhs(compiler, connection, lhs=fk_lhs)

        return (url_lhs_sql, url_params, fk_lhs_sql, fk_params)


@FkOrURLField.register_lookup
class Exact(FkOrURLFieldMixin, _Exact):
    """
    Determine which underlying field to use for the exact lookup.

    The RHS is either a remote or local FK, which can be mapped directly.
    """

    def get_prep_lookup(self):
        if self.rhs_is_direct_value():
            self.rhs = get_normalized_value(self.rhs)[0]
        return super().get_prep_lookup()

    def process_lhs(self, compiler, connection, lhs=None):
        (url_lhs_sql, url_params, fk_lhs_sql, fk_params) = self._split_lhs(
            compiler, connection, lhs=lhs
        )

        if isinstance(self.rhs, str):
            # dealing with a remote URL
            return (url_lhs_sql, url_params)
        else:
            return (fk_lhs_sql, fk_params)


@FkOrURLField.register_lookup
class In(FkOrURLFieldMixin, RelatedIn):
    """
    Split the IN query into two IN queries, per datatype.

    Creates an IN query for the url field values, and an IN query for the FK
    field values, joined together by an OR.
    """

    lookup_name = "in"

    def process_lhs(self, compiler, connection, lhs=None):
        return self._split_lhs(compiler, connection, lhs=lhs)

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
