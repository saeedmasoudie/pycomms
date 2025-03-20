from django.urls import path
from .consumers import WebRTCConsumer

websocket_urlpatterns = [
    path("ws/channel/<int:channel_id>/", WebRTCConsumer.as_asgi()),
]

