# Load Test Stub

This folder contains a k6 script (`k6_load.js`) that exercises the start and move endpoints. It is intended for manual/nightly runs—not per PR.

## Running locally

```
# Ensure backend is running (stub model is fine)
k6 run load_tests/k6_load.js
```

Environment variables:
- `BASE_URL` (default `http://localhost:8000`)
- `USERS` (default 5)
- `DURATION` (default `30s`)

## Targets (draft)
- `/api/games` p95 < 300ms
- `/api/games/{id}/moves` p95 < 500ms
- Error rate < 1% (exclude 4xx client errors)

Record results in PRs when running; adjust thresholds after baseline.
