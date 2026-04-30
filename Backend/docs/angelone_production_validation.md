# Angel One Production Validation

## Live Integration Command

```bash
cd Backend
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE>
```

Or use the wrapper:

```bash
cd Backend
./scripts/angelone_live_validation.py --client-code <CLIENT_CODE>
```

## Scenarios Covered

- `login_flow`
- `session_reuse`
- `token_refresh`
- `feed_token`
- `concurrent_session_validation`
- `logout_flow`

## Failure Injection

```bash
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE> --inject redis_down
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE> --inject broker_down
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE> --inject network_timeout
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE> --inject invalid_credentials
```

## Load Validation

```bash
./venv/bin/python manage.py validate_angelone_live --client-code <CLIENT_CODE> --concurrency 10 --iterations 20
```

Multi-client load:

```bash
printf "CLIENT1\nCLIENT2\nCLIENT3\n" > /tmp/angelone_clients.txt
./scripts/angelone_multi_client_load.py --client-file /tmp/angelone_clients.txt --parallel-clients 3 --concurrency 5 --iterations 10
```

## Production Sign-off Conditions

- All scenarios return `"status": "success"`
- No auth token / refresh token / feed token appears in logs
- Redis remains reachable and lock acquisition failures stay at zero
- Broker validation succeeds without repeated forced login storms
- Logout removes Redis session state and DB token state as expected
