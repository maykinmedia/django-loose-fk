=========
Changelog
=========

1.0.4 (2024-04-05)
==================

* Added setting ``LOOSE_FK_LOCAL_BASE_URLS``, which explicitly list allowed prefixes for
local urls to fine-tune resolving local and remote urls, now they can be hosted within
the same domain (#28).

1.0.3 (2023-07-14)
==================

* Fixed a bug which can appear when there is a chain of loose-fk objects, especially
when external object is related to the local one. In this case the local object was treated
like an external one, now it's fixed.
* Dropped support for Django 2.2

1.0.2 (2022-03-18)
==================

Bugfix release

* Fixed a bug in the django-filter implementation causing crashes on
  ``.filter(*args, **kwargs)`` calls because of tuples instead of ``models.Q`` objects
  being passed.

1.0.1 (2022-03-17)
==================

Bugfix / DRF version support release

* Fixed a bug in the custom field implementation on Django 3.2 when running ``Model.full_clean``
* Fixed support for djangorestframework 3.13
* The minimum supported DRF version is now 3.11

1.0.0 (2022-03-11)
==================

* Added support for Django 3.2
* Added support for Python 3.9 and 3.10
* Public API is now frozen

Breaking changes
----------------

On Django 3.2, there is a system check causing problems with the generated constraints:

.. code-block:: none

    ?: (models.E032) constraint name '_zaak_or_extern_zaak_filled' is not unique among models:
    testapp.ZaakObject, testapp.ZaakObject2.

The makemigrations should create a migration to drop the existing constraints and
generate new ones with unique names.

* Dropped support for Django 3.0
* Dropped support for Django 3.1
