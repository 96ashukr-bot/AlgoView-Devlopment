# Execution Node Architecture

## Overview

AlgoView now supports static-IP order execution through client-specific execution nodes.

```text
TradingView / Strategy Engine
        |
        v
Main Django Server
  - validates strategy and risk
  - creates ExecutionOrderJob
  - signs request with HMAC
        |
        v
ExecutionNode assigned to client
  - VPS with broker-whitelisted static IP
  - verifies HMAC and idempotency
  - places broker API order
        |
        v
Broker API sees client's static IP
```

## Onboarding Flow

1. Provision one VPS/static IP per client.
2. Add the VPS IP to the client's broker API whitelist.
3. Deploy the node worker code on that VPS.
4. Create the node on the main server:

```bash
python manage.py create_execution_node \
  --name "Client 101 Node" \
  --ip 203.0.113.10 \
  --server-url https://node-client-101.example.com \
  --provider aws \
  --node-id client-101-node \
  --secret "long-random-secret"
```

5. Assign it:

```bash
python manage.py assign_execution_node --client-id 101 --node-id client-101-node
```

6. Mark broker verification after the broker confirms the static IP:

```bash
python manage.py verify_execution_node --node-id client-101-node
```

## VPS Setup

Install the same Django backend or a compatible lightweight service implementing:

```text
POST /api/node/heartbeat/
POST /api/node/place-order/
GET  /api/node/health/
GET  /api/node/public-ip/
```

Required node environment:

```env
ALGOVIEW_NODE_MODE=true
ALGOVIEW_NODE_ID=client-101-node
ALGOVIEW_NODE_SECRET=long-random-secret
ALGOVIEW_MAIN_SERVER_IP=<main-server-public-ip>
NODE_ALLOWED_CLOCK_SKEW_SECONDS=60
NODE_REQUEST_TIMEOUT=10
```

## Main Server Environment

```env
ALGOVIEW_MAIN_SERVER_IP=<main-server-public-ip>
NODE_REQUEST_TIMEOUT=10
NODE_ALLOWED_CLOCK_SKEW_SECONDS=60
```

## Security Model

- Main server signs requests with HMAC SHA256.
- Signature input is `timestamp + "." + canonical_json_payload`.
- Node rejects requests with missing/bad signature.
- Node rejects timestamps outside `NODE_ALLOWED_CLOCK_SKEW_SECONDS`.
- Node rejects duplicate `X-ALGOVIEW-IDEMPOTENCY-KEY`.
- Broker credentials are not returned in API responses.
- Store node secrets using `ExecutionNode.set_node_secret()`.

## Firewall Rules

On every execution node, allow inbound HTTPS only from:

- `ALGOVIEW_MAIN_SERVER_IP`
- your admin SSH IP

Example UFW:

```bash
sudo ufw default deny incoming
sudo ufw allow from <main-server-ip> to any port 443 proto tcp
sudo ufw allow from <your-admin-ip> to any port 22 proto tcp
sudo ufw enable
```

## Client Broker IP Whitelist

For each client broker app/API console, whitelist:

```text
ExecutionNode.ip_address
```

Do not whitelist the main Django server for order placement. The main server should only coordinate and sign work.

## Order Routing

Application code should call:

```python
from main.services.execution_router import route_order_to_execution_node

route_order_to_execution_node(client, broker_details, order_payload)
```

The router creates `ExecutionOrderJob`, signs the request, sends it to:

```text
<node.server_url>/api/node/place-order/
```

The node broker adapter layer is wired for the same supported broker set as the main app:
Angel One, Upstox, Zerodha, Alice Blue, 5Paisa, FYERS, and Dhan. Each adapter reuses the
existing broker-specific order functions so static-IP execution follows the same symbol,
token, trade-history, and response handling paths as local execution.

## Troubleshooting

- `No execution node assigned`: assign a node to the client.
- `Execution node is not verified`: confirm broker whitelist and run `verify_execution_node`.
- `Invalid node request signature`: check node secret and clock sync.
- `Duplicate idempotency key`: resend with a new key only when you are sure the first order should be retried.
- `Execution node request timed out`: check node health, firewall, SSL, and gunicorn/uvicorn logs.
- Broker rejects order: inspect `ExecutionOrderJob.broker_response` and broker dashboard.

## Deployment Checklist

1. Run migrations on main server and each Django-based node.
2. Configure env vars.
3. Create execution node record.
4. Assign node to client.
5. Broker whitelist static IP.
6. Verify node.
7. Test health:

```bash
python manage.py test_execution_node --node-id client-101-node
```

8. Test broker adapter:

```bash
python manage.py test_broker_from_node --client-id 101
```
