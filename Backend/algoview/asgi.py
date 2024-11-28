"""
ASGI config for algoview project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoview.settings')

# application = get_asgi_application()

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from main import routing
# import main.routing  # You'll define your routing in routing.py
# /home/digiprima/Desktop/jyoti/Django/AlgoView-Devlopment/Backend/main/routing.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoview.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Define your WebSocket URLs
        )
    ),
})
