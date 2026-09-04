# celery.py
import os
import logging
from celery import Celery
from celery.signals import worker_init
from celery.schedules import crontab

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoview.settings')

app = Celery('algoview')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# Retain existing retry behavior on startup
app.conf.broker_connection_retry_on_startup = True
app.conf.beat_schedule = {
    **(getattr(app.conf, "beat_schedule", {}) or {}),
    "refresh-pre-market-broker-masters": {
        "task": "main.tasks.refresh_and_prewarm_broker_masters_task",
        "schedule": crontab(hour=7, minute=45, day_of_week="1-5"),
    },
    "recover-stale-manual-trade-results": {
        "task": "main.tasks.recover_stale_manual_trade_results_task",
        "schedule": 60.0,
        "options": {"queue": "priority_entry", "priority": 7},
    },
    "reconcile-durable-exit-intents": {
        "task": "main.tasks.reconcile_exit_intents_task",
        "schedule": 10.0,
        "options": {"queue": "priority_exit_dispatch", "priority": 9},
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
