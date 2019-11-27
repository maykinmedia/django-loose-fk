from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_allowed_hosts_wildcard(app_configs, **kwargs):
    if not any(pattern == "*" for pattern in settings.ALLOWED_HOSTS):
        return []

    return [
        Warning(
            "You have wildcards in your ALLOWED_HOSTS setting - "
            "this will cause all remote URLs to be considered local URLs and "
            "break django-loose-fk's behaviour.",
            obj=settings.ALLOWED_HOSTS,
            hint="You should use an explicit list of domains *without* wildcards.",
            id="django_loose_fk.W001",
        )
    ]
