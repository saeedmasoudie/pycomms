import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import pycomms.routing

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pycomms.settings')
django.setup()

# ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            pycomms.routing.websocket_urlpatterns
        )
    ),
})
