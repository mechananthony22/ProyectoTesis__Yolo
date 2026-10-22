"""Servidor efímero para pruebas visuales; nunca usar en producción."""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
os.environ['DJANGO_SETTINGS_MODULE']='config.test_settings'
import django
from django.conf import settings
folder=Path(tempfile.mkdtemp(prefix='hasslab-smoke-'))
settings.DATABASES['default']['NAME']=str(folder/'db.sqlite3')
settings.MEDIA_ROOT=folder/'media'
settings.ALLOWED_HOSTS=['localhost','127.0.0.1','testserver']
django.setup()
from django.core.management import call_command
from apps.accounts.models import User
call_command('migrate',verbosity=0)
User.objects.create_superuser('smoke','smoke@example.test','Smoke-only-password-29')
print('Smoke user created in temporary database. Do not use for research.',flush=True)
call_command('runserver','127.0.0.1:8000',use_reloader=False)
