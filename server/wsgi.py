"""
WSGI config for Athena project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import sys
sys.path.append('/home/song/proj/b/Athena')

from django.core.wsgi import get_wsgi_application

os.environ["DJANGO_SETTINGS_MODULE"] = "Athena.settings"

activate_env=os.path.expanduser("/home/song/.virtualenvs/Athena/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))
application = get_wsgi_application()
