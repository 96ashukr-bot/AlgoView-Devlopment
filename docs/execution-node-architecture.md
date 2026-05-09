# Execution Node Architecture

## Overview

AlgoView supports broker-agnostic static-IP execution using two execution route types:

```text
client_id -> execution_node -> execution_type -> broker_registry -> broker_adapter -> broker API
```

No live order should bypass `main.services.execution_router.route_order_to_execution_node`.

## VPS Node Mode

```text
Main AlgoView Server
    -> Client VPS Execution Node
    -> Broker API
    -> Client trading account
```

The main server validates strategy/risk, creates an `ExecutionOrderJob`, signs the payload with HMAC, and posts it to:

```text
<node.server_url>/api/node/place-order/
```

The remote node verifies the signature/idempotency key and places the broker order from its own static IP.

## Proxy Mode

```text
Main AlgoView Server
    -> Assigned static proxy host:port
    -> Broker API
    -> Client trading account
```

The main server places the broker request directly, but every broker HTTP request is made with `proxies=proxy_config`.
Broker adapters that cannot safely guarantee proxy usage must set `supports_proxy = False`; proxy trading is blocked for those adapters.

Vendor proxy fields map as:

```text
Hostname/Postname/Proxy host -> proxy_host
Port number                 -> proxy_port
User ID                     -> proxy_username
Password                    -> proxy_password
Visible static IPv4/IPv6    -> ip_address
```

## Verification

For proxy mode, AlgoView verifies the outgoing proxy IP with:

- `https://api.ipify.org?format=json`
- `https://ifconfig.me/ip`
- `https://checkip.amazonaws.com`

The returned IP must match `ExecutionNode.ip_address`. Proxy-mode live trading is blocked unless:

- `is_active=True`
- `assigned_client` is the trading client
- `is_verified_with_broker=True`
- `proxy_public_ip_verified=True`

## Broker Registry

Broker routing uses `main.brokers.registry.get_broker_adapter()`.

Adapters must implement:

```python
login(proxy_config=None)
place_order(payload, proxy_config=None)
modify_order(payload, proxy_config=None)
cancel_order(payload, proxy_config=None)
get_orderbook(proxy_config=None)
get_positions(proxy_config=None)
get_holdings(proxy_config=None)
validate_credentials(proxy_config=None)
```

HTTP-based adapters can support proxy mode by passing `proxy_config` to every `requests` call. SDK-based adapters must only enable proxy mode after verifying that the SDK supports proxy/session injection.

Current proxy-enabled adapters:

- Upstox
- FYERS
- 5Paisa

Current adapters blocked in proxy mode until direct proxy support is implemented:

- Angel One SmartConnect
- Alice Blue pya3
- Zerodha Kite SDK
- Dhan SDK

## Management Commands

Create VPS node:

```bash
python manage.py create_execution_node \
  --name "Client 101 VPS" \
  --ip 203.0.113.10 \
  --execution-type vps_node \
  --server-url https://node-client-101.example.com \
  --provider aws \
  --node-id client-101-node \
  --node-secret "long-random-secret"
```

Create proxy route:

```bash
python manage.py create_execution_node \
  --name "Client 101 Proxy" \
  --ip 203.0.113.20 \
  --execution-type proxy \
  --provider proxy-vendor \
  --proxy-protocol http \
  --proxy-host proxy.vendor.example \
  --proxy-port 8080 \
  --proxy-username user \
  --proxy-password "secret"
```

Verify proxy IP:

```bash
python manage.py verify_execution_proxy --node-id client-101-node
```

Assign/release:

```bash
python manage.py assign_execution_node --client-id 101 --node-id client-101-node
python manage.py release_execution_node --client-id 101
```

Broker tests:

```bash
python manage.py test_broker_from_node --client-id 101
python manage.py test_proxy_broker_login --client-id 101
python manage.py test_proxy_orderbook --client-id 101
```

## Security

- `node_secret` and `proxy_password` are encrypted with the existing credential crypto utility.
- API serializers never return node secrets or proxy passwords.
- Logs store only masked proxy URLs.
- HMAC signing protects VPS node requests.
- Idempotency keys protect node order replay.
- Firewall VPS nodes to allow HTTPS only from `ALGOVIEW_MAIN_SERVER_IP`.

## Troubleshooting

- Returned IP mismatch: vendor may have supplied a rotating proxy, wrong port, or IPv4/IPv6 mismatch.
- Proxy auth failed: check username/password and whether the vendor expects IP auth instead.
- Broker rejects IP: whitelist the visible static IP, not the proxy hostname.
- SDK bypasses proxy: use VPS mode or implement a direct HTTP adapter with proxy support.
- High latency/timeouts: increase vendor region proximity or lower order route timeout expectations.
- Existing VPS node stopped: check `last_heartbeat`, node logs, firewall, SSL, and gunicorn/uvicorn.
