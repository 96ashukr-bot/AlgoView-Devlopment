# Pending BUY and SELL timeout — older AlgoView only

## Behavior

`PENDING_ORDER_TIMEOUT_ENABLED` defaults to `False`. This feature is not active merely because its source files are installed. No SaaS files or settings are involved.

When enabled, a Celery sweep runs every five seconds and registers system history rows with an exact broker order ID and pending BUY or SELL status. It does not import or cancel unrelated broker/manual orders. A dedicated worker confirms the current order status, side, quantities, assigned broker route, and same-day token policy before requesting cancellation of an unfilled remainder.

The deadline is 60 seconds after broker order creation. When creation time is unavailable, it is 60 seconds after first observation. Deadlines and processing leases are stored in the database and survive worker restarts. Under healthy conditions the next sweep processes overdue orders; queue load, broker latency, unavailable sessions or rate limits can delay cancellation. Cancellation is not guaranteed at exactly the 60th second. Existing pending orders older than 60 seconds are eligible on activation. Recognized trigger-pending orders are included.

- A zero-fill BUY cancellation removes the provisional entry quantity and price; it is not a closed position.
- A partially filled BUY retains the actual purchased quantity and broker average price.
- A zero-fill or partial SELL cancellation leaves the remaining BUY position open, marked for review. It does not submit a replacement SELL. The next explicit exit uses the remaining quantity.
- A SELL that fills during cancellation is reconciled using confirmed fills and their prices, with explicit linkage to the original BUY. A cancellation response alone never marks a position closed.
- Unknown status, unknown fill quantity, changed order identity, missing proxy, and invalid same-day authentication block cancellation. Tokens are never regenerated or bypassed by this monitor.
- Each cancellation request is followed by another exact-order read. Up to three attempts are permitted, each preceded by a fresh check. An unconfirmed order then requires review. Persisted `last_error`, `last_snapshot`, attempt count and state show the reason.

Adapters cover Zerodha, Upstox, Angel One, Alice Blue, Dhan, FYERS, Groww and 5paisa. Broker endpoints and normalization are covered by mocks; live cancellation acceptance has not been tested. Unsupported/special order varieties fail closed.

## Installation and activation

Use only the old application at `/var/www/sparkbridge/Backend` (3.109.40.137). Review and deploy the complete change together, including migration `0032_pending_order_timeouts`, the partial-fill position guard/reconciliation changes, Celery tasks and schedule, and `deploy/sparkbridge-pending-order-timeout.service`.

1. Keep `PENDING_ORDER_TIMEOUT_ENABLED=False` while installing and run `venv/bin/python manage.py migrate` and `venv/bin/python manage.py check` in the old Backend directory.
2. Install the supplied worker unit in `/etc/systemd/system/` and reload systemd. It consumes only the `pending_order_timeout` queue. Keep one Celery Beat scheduler for this application.
3. To activate, the operator sets `PENDING_ORDER_TIMEOUT_ENABLED=True` in the old Backend `.env`, starts/enables `sparkbridge-pending-order-timeout.service`, and restarts `sparkbridge-celery-beat.service`. Restart existing order/reconciliation workers and application services to load the accompanying partial-fill changes.
4. Check the worker and Beat logs, and inspect the `PendingOrderTimeout` records. `WAITING`, `CANCEL_REQUESTED` and `RETRY` are active states; `TERMINAL` has broker confirmation; `ATTENTION` requires operator review. No broker credentials are stored in these records.

To stop future monitor requests, stop the dedicated worker and set the flag to `False`; already submitted broker cancellations cannot be undone. Retain the database table and audit records.

## Local verification

Use an isolated SQLite test database with mocked broker requests. Do not invoke the worker task against production as a test. Tests cover the deadline boundary for both sides, restart recovery, duplicates, leases, broker identity changes, authentication rejection, partial fills, fill/cancel races, ambiguous API responses and disabled behavior. Existing lifecycle fixtures explicitly update historical dates after creation because the model uses `auto_now_add`.
