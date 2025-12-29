"""
WSGI config for cobblemon_panel project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cobblemon_panel.settings')

application = get_wsgi_application()

