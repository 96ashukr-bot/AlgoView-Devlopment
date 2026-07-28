# celery.py
import os
import logging
from celery import Celery
from celery.signals import worker_init, worker_ready

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoview.settings')

app = Celery('algoview')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# Retain existing retry behavior on startup
app.conf.broker_connection_retry_on_startup = True
app.conf.beat_schedule = {
    **(getattr(app.conf, "beat_schedule", {}) or {}),
    "warm-active-angel-sessions": {
        "task": "main.tasks.warm_active_angel_sessions_task",
        "schedule": 300.0,
    },
}


@worker_init.connect(dispatch_uid="sparkbridge.prewarm_angel_contract_master")
def prewarm_angel_contract_master(**_kwargs):
    """Build Angel's shared in-memory index before worker pool processes fork."""
    try:
        from main.angelone.managers.contract_manager import ContractMasterManager

        ContractMasterManager.get_instance().initialize(blocking=False)
    except Exception:
        # Worker startup must remain available; the order path retains its
        # durable-cache/API fallback if prewarming cannot complete.
        logger.exception("Angel contract-master prewarm failed")


@worker_ready.connect(dispatch_uid="sparkbridge.warm_angel_sessions")
def warm_angel_sessions_on_worker_ready(**_kwargs):
    """Start one non-blocking session warmup whenever execution workers restart."""
    try:
        from main.tasks import warm_active_angel_sessions_task

        warm_active_angel_sessions_task.delay()
    except Exception:
        logger.exception("Angel session warmup dispatch failed")
