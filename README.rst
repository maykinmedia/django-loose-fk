===============
Django Loose FK
===============

:Version: 1.0.4
:Source: https://github.com/maykinmedia/django-loose-fk
:Keywords: ``ForeignKey``, ``URL reference``, ``decentralization``, ``integrity``

|build-status| |code-quality| |black| |coverage|

|python-versions| |django-versions| |pypi-version|

Django Loose FK handles local or remote "ForeignKey" references.

In a decentralized API landscape various providers can offer the same type of
data, while your own API also provides this. The django model field allows
you to handle this transparently and present a unified, clean Python API.

.. contents::

.. section-numbering::

Features
========

* Always work with Django model instances
* Automatically added check constraints
* Pluggable interface to fetch remote objects
* Automatically supports DRF Hyperlinked serializers and serializer fields

Installation
============

Requirements
------------

* Python 3.7 or above
* setuptools 30.3.0 or above
* Django 3.2 or newer


Install
-------

.. code-block:: bash

    pip install django-loose-fk

.. warning::

    You must also make sure ``ALLOWED_HOSTS`` is a list of actual domains, and not
    a wildcard. When loose-fk gets a URL to load, it first looks up if the domain
    is a local domain and if so, will load the actual local database record.

Usage
=====

At the core sits a (virtual) django model field.

.. code-block:: python

    from django_loose_fk.fields import FkOrURLField

    class SomeModel(models.Model):
        name = models.CharField(max_length=100)


    class OtherModel(models.Model):
        local = models.ForeignKey(SomeModel, on_delete=models.CASCADE, blank=True, null=True)
        remote = models.URLField(blank=True)
        relation = FkOrURLField(fk_field="local", url_field="remote")


You can now create objects with either local instances or URLs:

.. code-block:: python

    some_local = SomeModel.objects.get()
    OtherModel.objects.create(relation=some_local)

    OtherModel.objects.create(relation="https://example.com/remote.json")


Accessing the attribute will always yield an instance:

.. code-block:: python

    >>> other = OtherModel.objects.get(id=1)  # local FK
    >>> other.relation
    <SomeModel (pk: 1)>

    >>> other = OtherModel.objects.get(id=2)  # remote URL
    >>> other.relation
    <SomeModel (pk: None)>

In the case of a remote URL, the URL will be fetched and the JSON response used
as init kwargs for a model instance. The ``.save()`` method is blocked for
remote instances to prevent mistakes.

Loaders
-------

Loaders are pluggable interfaces to load data. The default loader is
``django_loose_fk.loaders.RequestsLoader``, which depends on the ``requests``
library to fetch the data.

You can specify a global default loader with the setting ``DEFAULT_LOOSE_FK_LOADER``

.. code-block:: python

    DEFAULT_LOOSE_FK_LOADER = "django_loose_fk.loaders.RequestsLoader"

or override the loader on a per-field basis:

.. code-block:: python

    from django_loose_fk.loaders import RequestsLoader

    class MyModel(models.Model):
        ...

        relation = FkOrURLField(
            fk_field="local",
            url_field="remote",
            loader=RequestsLoader()
        )

Local and remote urls
---------------------

If several services are hosted within the same domain, it could be tricky to separate
local and remote urls. In this case an additional setting ``LOOSE_FK_LOCAL_BASE_URLS`` can be used
to define an explicit list of allowed prefixes for local urls.

.. code-block:: python

    LOOSE_FK_LOCAL_BASE_URLS = [
        "https://api.example.nl/ozgv-t/zaken/",
        "https://api.example.nl/ozgv-t/catalogi/",
    ]


.. |build-status| image:: https://github.com/maykinmedia/django-loose-fk/workflows/Run%20CI/badge.svg
    :alt: Build status
    :target: https://github.com/maykinmedia/django-loose-fk/actions?query=workflow%3A%22Run+CI%22

.. |code-quality| image:: https://github.com/maykinmedia/django-loose-fk/workflows/Code%20quality%20checks/badge.svg
     :alt: Code quality checks
     :target: https://github.com/maykinmedia/django-loose-fk/actions?query=workflow%3A%22Code+quality+checks%22

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |coverage| image:: https://codecov.io/gh/maykinmedia/django-loose-fk/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/django-loose-fk
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/django-loose-fk.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/django-loose-fk.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/django-loose-fk.svg
    :target: https://pypi.org/project/django-loose-fk/
