# celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoview.settings')

app = Celery('algoview')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# Retain existing retry behavior on startup
app.conf.broker_connection_retry_on_startup = True