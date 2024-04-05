"""
Test django_loose_fk.utils.is_local function with various
combinations of settings
"""

from django.test import override_settings

from django_loose_fk.utils import is_local


@override_settings(
    LOOSE_FK_LOCAL_BASE_URLS=["http://api.example.nl/ozgv-t/zaken"],
)
def test_with_setting_same_host_same_prefix():
    assert (
        is_local(host="api.example.nl", url="http://api.example.nl/ozgv-t/zaken/1")
        is True
    )


@override_settings(
    LOOSE_FK_LOCAL_BASE_URLS=["http://api.example.nl/ozgv-t/zaken"],
)
def test_with_setting_same_host_diff_prefix():
    assert (
        is_local(host="api.example.nl", url="http://api.example.nl/ozgv-t/documenten/1")
        is False
    )


@override_settings(
    LOOSE_FK_LOCAL_BASE_URLS=["http://otherapi.example.nl/ozgv-t/zaken"],
)
def test_with_setting_diff_host():
    assert (
        is_local(host="api.example.nl", url="http://otherapi.example.nl/ozgv-t/zaken/1")
        is True
    )


def test_no_setting_same_host_with_prefix():
    assert (
        is_local(host="api.example.nl", url="http://api.example.nl/ozgv-t/zaken/1")
        is True
    )


def test_no_setting_same_host_no_prefix():
    assert is_local(host="api.example.nl", url="http://api.example.nl/zaken/1") is True


def test_no_setting_diff_host():
    assert (
        is_local(host="api.example.nl", url="http://otherapi.example.nl/ozgv-t/zaken/1")
        is False
    )
