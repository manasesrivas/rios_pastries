"""
ASGI config for rios_pastries_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import orders
import orders.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rios_pastries_backend.settings')

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': AuthMiddlewareStack(
            URLRouter(
                orders.routing.websocket_urlpatterns
            )
        )
    }
)
