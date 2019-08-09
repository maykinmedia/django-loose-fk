import pytest

from django_loose_fk.query_list import QueryList, is_url


@pytest.mark.parametrize(
    "value", ("foo", 1, None, "ftp://example.com/bad-scheme", "http://testserver/foo")
)
def test_invalid_urls(value):
    assert is_url(value) is False


@pytest.mark.parametrize(
    "value", ("https://example.com", "http://example.com/foo", "http://sub.example.com")
)
def test_valid_urls(value):
    assert is_url(value) is True


def test_querylist_iteration():
    items = ["foo", "bar"]
    ql = QueryList(items)

    assert [item for item in ql] == items


def test_querylist_containment():
    ql = QueryList(["foo", "bar"])

    assert "foo" in ql
    assert "baz" not in ql


@pytest.mark.parametrize("items,expected", [(["foo", "bar"], "foo"), ([], None)])
def test_element_retrieval_first(items, expected):
    ql = QueryList(items)

    assert ql.first() == expected


def test_querylist_count():
    ql = QueryList(["foo", "bar"])

    assert ql.count() == 2
