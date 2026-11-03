from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/notificaciones/?$', consumers.NoticationsConsumer.as_asgi()),
]