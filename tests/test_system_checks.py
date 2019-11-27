import pytest

from django_loose_fk.checks import check_allowed_hosts_wildcard


def test_default_test_settings_ok():
    errors = check_allowed_hosts_wildcard(None)

    assert errors == []


@pytest.mark.parametrize("host", ["*.example.com", "localhost", "foo.example.com"])
def test_valid_settings_ok(host, settings):
    settings.ALLOWED_HOSTS = [host]

    errors = check_allowed_hosts_wildcard(None)

    assert errors == []


@pytest.mark.parametrize("hosts", [["*"], ["localhost", "*"]])
def test_settings_wrong(hosts, settings):
    settings.ALLOWED_HOSTS = hosts

    errors = check_allowed_hosts_wildcard(None)

    assert len(errors) == 1
    assert errors[0].id == "django_loose_fk.W001"
