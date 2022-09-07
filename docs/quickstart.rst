==========
Quickstart
==========

Installation
============

Install from PyPI with pip:

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


Handlers
--------

As mentioned before when ``FkOrURLField`` attribute is accesses the (virtual) model
instance is always returned. However this instance can include relation fields such
as ``ForeignKey`` and ``ManyToManyField``. In case of remote urls we use handlers
to access the relation fields.

You can specify a global default mapping of relation fields and handlers with the
setting ``DEFAULT_LOOSE_FK_HANDLERS``:

.. code-block:: python

    DEFAULT_LOOSE_FK_HANDLERS = "django_loose_fk.virtual_models.HANDLERS"

