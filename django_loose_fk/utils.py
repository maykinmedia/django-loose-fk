from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.urls import Resolver404, get_resolver

from rest_framework import viewsets
from rest_framework.request import Request


def get_viewset_for_path(path: str) -> viewsets.ViewSet:
    """
    Look up which viewset matches a path.
    """
    # NOTE: this doesn't support setting a different urlconf on the request
    resolver = get_resolver()
    try:
        resolver_match = resolver.resolve(path)
    except Resolver404 as exc:
        raise models.ObjectDoesNotExist("URL did not resolve") from exc
    callback, callback_args, callback_kwargs = resolver_match

    # TODO: add support for APIView
    assert hasattr(callback, "cls"), "Callback doesn't appear to be from a viewset"

    viewset = callback.cls(**callback.initkwargs)
    viewset.action_map = callback.actions
    viewset.request = Request(HttpRequest())
    viewset.args = callback_args
    viewset.kwargs = callback_kwargs

    return viewset


def get_resource_for_path(path: str) -> models.Model:
    """
    Retrieve the API instance belonging to a (detail) path.
    """
    if settings.FORCE_SCRIPT_NAME and path.startswith(settings.FORCE_SCRIPT_NAME):
        path = path[len(settings.FORCE_SCRIPT_NAME) :]
    viewset = get_viewset_for_path(path)

    queryset = viewset.get_queryset()
    lookup_url_kwarg = viewset.lookup_url_kwarg or viewset.lookup_field
    filter_kwargs = {viewset.lookup_field: viewset.kwargs[lookup_url_kwarg]}

    return queryset.get(**filter_kwargs)


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass
