"""
ASGI config for sports_gala project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development'))

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()


class LazyWebSocketApplication:
    def __init__(self):
        self._app = None

    async def __call__(self, scope, receive, send):
        if self._app is None:
            from core import routing as core_routing
            self._app = AllowedHostsOriginValidator(
                AuthMiddlewareStack(
                    URLRouter(core_routing.websocket_urlpatterns)
                )
            )
        return await self._app(scope, receive, send)

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler with authentication
    "websocket": LazyWebSocketApplication(),
})
