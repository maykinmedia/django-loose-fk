.. django_loose_fk documentation master file, created by startproject.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-loose-fk's documentation!
===========================================

|build-status| |code-quality| |black| |coverage|

|python-versions| |django-versions| |pypi-version|

Django Loose FK handles local or remote "ForeignKey" references.

In a decentralized API landscape various providers can offer the same type of
data, while your own API also provides this. The django model field allows
you to handle this transparently and present a unified, clean Python API.

Features
========

* Always work with Django model instances
* Automatically added check constraints
* Pluggable interface to fetch remote objects
* Automatically supports DRF Hyperlinked serializers and serializer fields

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


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
