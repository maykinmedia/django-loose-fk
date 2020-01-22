===============
Django Loose FK
===============

:Version: 0.7.0
:Source: https://github.com/maykinmedia/django-loose-fk
:Keywords: ``ForeignKey``, ``URL reference``, ``decentralization``, ``integrity``
:PythonVersion: 3.7

|build-status| |requirements| |coverage|

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
* Pluggable interface to fetch remote objects
* Automatically supports DRF Hyperlinked serializers and serializer fields

Installation
============

Requirements
------------

* Python 3.7 or above
* setuptools 30.3.0 or above
* Django 2.0 or newer


Install
-------

.. code-block:: bash

    pip install django-loose-fk

.. warning::

    You must also make sure ``ALLOWED_HOSTS`` is a list of actual domains, and not
    a wildcard. When loose-fk gets a URL to load, it first looks up if the domain
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



.. |build-status| image:: https://travis-ci.org/maykinmedia/django-loose-fk.svg?branch=develop
    :target: https://travis-ci.org/maykinmedia/django-loose-fk

.. |requirements| image:: https://requires.io/github/maykinmedia/django-loose-fk/requirements.svg?branch=develop
    :target: https://requires.io/github/maykinmedia/django-loose-fk/requirements/?branch=develop
    :alt: Requirements status

.. |coverage| image:: https://codecov.io/gh/maykinmedia/django-loose-fk/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/django-loose-fk
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/django-loose-fk.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/django-loose-fk.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/django-loose-fk.svg
    :target: https://pypi.org/project/django-loose-fk/
