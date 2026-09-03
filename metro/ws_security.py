"""WebSocket origin validation for the ASGI stack.

``AllowNativeClientsOriginValidator`` behaves like Channels'
``AllowedHostsOriginValidator`` for browser clients (the ``Origin`` header must
match ``settings.ALLOWED_HOSTS``), which is what blocks cross-site WebSocket
hijacking. It additionally lets through connections that send *no* ``Origin``
header at all -- native mobile apps and other non-browser clients -- since those
are not subject to the browser same-origin threat model.
"""

from channels.security.websocket import OriginValidator
from django.conf import settings


class AllowNativeClientsOriginValidator(OriginValidator):
    def __init__(self, application):
        allowed_hosts = list(settings.ALLOWED_HOSTS)
        if settings.DEBUG and not allowed_hosts:
            allowed_hosts = ["localhost", "127.0.0.1", "[::1]"]
        super().__init__(application, allowed_hosts)

    def valid_origin(self, parsed_origin):
        # No Origin header -> non-browser client -> allow.
        if parsed_origin is None:
            return True
        return super().valid_origin(parsed_origin)
