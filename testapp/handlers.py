from django.db import models

from django_loose_fk.virtual_models import BaseHandler


class DummyHandler(BaseHandler):
    def __get__(self, instance, cls=None):
        return "dummy"


HANDLERS = {models.ForeignKey: DummyHandler}
