"""WebSocket URL routing for Django Channels"""
from django.urls import re_path
from core.consumers import DashboardConsumer, GameConsumer

websocket_urlpatterns = [
    # Public dashboard WebSocket
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
    
    # Game-specific WebSocket
    re_path(r'ws/game/(?P<game_id>\d+)/$', GameConsumer.as_asgi()),
]
