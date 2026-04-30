"""
Celery Tasks for Async Order Execution
======================================
Queue-based order execution for scalability.

Features:
- Async order placement
- Priority queues
- Retry logic
- Multi-client support
"""

from celery import shared_task, Task
from celery.utils.log import get_task_logger
from typing import Dict, Any, Optional
import time

from .utils.logging_utils import TradingLogger, set_request_context
from .utils.idempotency import get_idempotency_manager
from .managers.session_manager import SessionManager
from .managers.position_manager import PositionManager, PositionSide
from .managers.contract_manager import ContractMasterManager
from .services.ltp_service import LTPService
from .constants import ORDER_QUEUE_NAME

logger = TradingLogger("celery_tasks")
celery_logger = get_task_logger(__name__)


class OrderTask(Task):
    """Base task with error handling"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 1}
    retry_backoff = True
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Task failed",
            task_id=task_id,
            error=str(exc),
            args=args
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            "Task completed",
            task_id=task_id
        )


@shared_task(
    bind=True,
    base=OrderTask,
    name='angelone.place_order',
    queue=ORDER_QUEUE_NAME,
    priority=5
)
def place_order_async(
    self,
    client_id: str,
    api_key: str,
    order_params: Dict[str, Any],
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async order placement task.
    
    Args:
        client_id: Client ID
        api_key: API key
        order_params: Order parameters
        request_id: Request tracking ID
        
    Returns:
        Order result dict
    """
    set_request_context(request_id=request_id, client_id=client_id)
    
    logger.info(
        "Processing order task",
        task_id=self.request.id,
        client_id=client_id,
        symbol=order_params.get('tradingsymbol')
    )
    
    try:
        # Get session
        session_manager = SessionManager.get_instance()
        session = session_manager.get_session(client_id, api_key)
        
        if not session or not session.is_valid():
            return {
                "status": "error",
                "message": "Invalid or expired session",
                "task_id": self.request.id
            }
        
        smart_connect = session.smart_connect
        
        # Check idempotency
        idempotency_manager = get_idempotency_manager()
        is_duplicate, existing = idempotency_manager.check_duplicate(
            client_id=client_id,
            symbol=order_params.get('tradingsymbol', ''),
            strike=order_params.get('strike'),
            side=order_params.get('transactiontype', 'BUY'),
            quantity=int(order_params.get('quantity', 1)),
            option_type=order_params.get('option_type')
        )
        
        if is_duplicate:
            return {
                "status": "duplicate",
                "message": "Duplicate order detected",
                "existing_order_id": existing.order_id if existing else None,
                "task_id": self.request.id
            }
        
        # Place order
        result = smart_connect.placeOrder(order_params)
        
        if result.get("status"):
            order_id = result.get("data", {}).get("orderid")
            
            # Record execution
            if existing:
                idempotency_manager.record_execution(
                    existing.idempotency_key,
                    order_id,
                    "complete"
                )
            
            # Update position
            position_manager = PositionManager.get_instance()
            side = order_params.get('transactiontype', 'BUY')
            
            position_manager.add_position(
                client_id=client_id,
                symbol=order_params.get('tradingsymbol', ''),
                underlying=order_params.get('underlying', ''),
                side=PositionSide.LONG if side == 'BUY' else PositionSide.SHORT,
                quantity=int(order_params.get('quantity', 1)),
                price=float(order_params.get('price', 0)),
                strike=order_params.get('strike'),
                option_type=order_params.get('option_type'),
                order_id=order_id
            )
            
            logger.info(
                "Order placed successfully",
                order_id=order_id,
                client_id=client_id
            )
            
            return {
                "status": "success",
                "order_id": order_id,
                "message": "Order placed successfully",
                "task_id": self.request.id
            }
        else:
            error_msg = result.get("message", "Order placement failed")
            
            # Remove idempotency record on failure
            if existing:
                idempotency_manager.remove_record(existing.idempotency_key)
            
            logger.error(
                "Order placement failed",
                client_id=client_id,
                error=error_msg
            )
            
            return {
                "status": "error",
                "message": error_msg,
                "task_id": self.request.id
            }
            
    except Exception as e:
        logger.exception(
            "Order task exception",
            client_id=client_id,
            error=str(e)
        )
        raise


@shared_task(
    bind=True,
    base=OrderTask,
    name='angelone.place_order_batch',
    queue=ORDER_QUEUE_NAME,
    priority=3
)
def place_order_batch_async(
    self,
    orders: list,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Batch order placement for multiple clients.
    
    Args:
        orders: List of order dicts with client_id, api_key, order_params
        request_id: Request tracking ID
        
    Returns:
        Batch result dict
    """
    set_request_context(request_id=request_id)
    
    logger.info(
        "Processing batch order task",
        task_id=self.request.id,
        order_count=len(orders)
    )
    
    results = []
    
    for order in orders:
        try:
            result = place_order_async.apply(
                args=[
                    order['client_id'],
                    order['api_key'],
                    order['order_params']
                ],
                kwargs={'request_id': request_id}
            )
            results.append({
                "client_id": order['client_id'],
                "result": result.get()
            })
        except Exception as e:
            results.append({
                "client_id": order['client_id'],
                "result": {"status": "error", "message": str(e)}
            })
    
    success_count = sum(1 for r in results if r['result'].get('status') == 'success')
    
    return {
        "status": "complete",
        "total": len(orders),
        "success": success_count,
        "failed": len(orders) - success_count,
        "results": results,
        "task_id": self.request.id
    }


@shared_task(
    name='angelone.refresh_contract_master',
    queue='angelone_maintenance'
)
def refresh_contract_master_async() -> Dict[str, Any]:
    """Background task to refresh contract master"""
    logger.info("Refreshing contract master via task")
    
    try:
        manager = ContractMasterManager.get_instance()
        success = manager._refresh_contracts()
        
        return {
            "status": "success" if success else "error",
            "contract_count": manager.contract_count,
            "last_refresh": manager.last_refresh.isoformat() if manager.last_refresh else None
        }
    except Exception as e:
        logger.error("Contract master refresh task failed", error=str(e))
        return {"status": "error", "message": str(e)}


@shared_task(
    name='angelone.cleanup_sessions',
    queue='angelone_maintenance'
)
def cleanup_sessions_async() -> Dict[str, Any]:
    """Background task to cleanup expired sessions"""
    logger.info("Cleaning up expired sessions")
    
    try:
        manager = SessionManager.get_instance()
        initial_count = len(manager._sessions)
        
        # Trigger cleanup
        manager._cleanup_loop.__wrapped__(manager, 0)
        
        final_count = len(manager._sessions)
        
        return {
            "status": "success",
            "cleaned": initial_count - final_count,
            "remaining": final_count
        }
    except Exception as e:
        logger.error("Session cleanup task failed", error=str(e))
        return {"status": "error", "message": str(e)}
