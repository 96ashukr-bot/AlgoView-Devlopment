# AWS VPS execution node

This mode is separate from the existing Execution IP/proxy mode. Do not alter
proxy records when provisioning a VPS node.

## Requirements

- Use an EC2 Elastic IP; do not depend on an auto-assigned address.
- Deploy the same backend release as the main AlgoView server.
- Connect the node to the same PostgreSQL database and Redis service.
- Configure the same `BROKER_ENCRYPTION_KEYS` so the node can read the assigned
  client's broker credentials.
- Terminate TLS at Nginx and allow inbound HTTPS only from the main AlgoView
  server. Allow outbound HTTPS to broker APIs.
- Keep the instance clock synchronized with NTP because signed requests have a
  limited clock skew.

## Node environment

```env
ALGOVIEW_NODE_MODE=True
ALGOVIEW_NODE_ID=client-493-aws-node
ALGOVIEW_NODE_SECRET=replace-with-a-long-random-secret
ALGOVIEW_MAIN_SERVER_URL=https://admin.algoview.in
ALGOVIEW_MAIN_SERVER_IP=MAIN_SERVER_PUBLIC_IP
```

The Node ID and Node Secret must exactly match the VPS Node record in AlgoView.
Set Server URL to the node's HTTPS origin without an API suffix, for example
`https://node-493.example.com`.

## Verification

```bash
python manage.py check
python manage.py run_execution_node_heartbeat --once
curl https://node-493.example.com/api/node/health/
```

The health response must report `node_mode: true` and the configured Node ID.
Install and enable `deploy/sparkbridge-execution-node-heartbeat.service`, then
use AlgoView's node health and broker-login tests before enabling live orders.

Orders are HMAC-signed, carry an idempotency key, and are accepted only when
the receiving server is in node mode and the supplied Node ID matches its own
configuration.
