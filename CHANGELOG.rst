=========
Changelog
=========

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
