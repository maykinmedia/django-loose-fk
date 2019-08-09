from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    validator = URLValidator(schemes=["http", "https"])
    try:
        validator(value)
    except ValidationError:
        return False

    return True


class QueryList:
    def __init__(self, items: list):
        self.items = items

    def __repr__(self):
        return f"<QueryList items={repr(self.items)}>"

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, item):
        # treat URls specially (for now at least)
        if not is_url(item):
            return item in self.items

        urls = (_item._loose_fk_data.get("url") for _item in self.items)
        return item in urls

    def get(self):
        assert len(self.items) == 1
        return self.items[0]

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self

    def count(self):
        return len(self.items)

    def filter(self, *expressions, **filters) -> "QueryList":
        raise NotImplementedError

    def exclude(self, *expressions, **filters) -> "QueryList":
        raise NotImplementedError
