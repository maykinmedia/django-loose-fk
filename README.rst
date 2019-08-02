===============
Django Loose FK
===============

:Version: 0.1.0
:Source: https://github.com/maykinmedia/django_loose_fk
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

    pip install django_loose_fk


Usage
=====

<document or refer to docs>


.. |build-status| image:: https://travis-ci.org/maykinmedia/django_loose_fk.svg?branch=develop
    :target: https://travis-ci.org/maykinmedia/django_loose_fk

.. |requirements| image:: https://requires.io/github/maykinmedia/django_loose_fk/requirements.svg?branch=develop
    :target: https://requires.io/github/maykinmedia/django_loose_fk/requirements/?branch=develop
    :alt: Requirements status

.. |coverage| image:: https://codecov.io/gh/maykinmedia/django_loose_fk/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/django_loose_fk
    :alt: Coverage status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/django_loose_fk.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/django_loose_fk.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/django_loose_fk.svg
    :target: https://pypi.org/project/django_loose_fk/
