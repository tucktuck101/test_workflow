# Runbooks (MVP)

## Startup/Deployment Checklist
- Set env vars from `.env` or deployment config (`MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE`, ports).
- Ensure model artifact exists and hash matches.
- Start backend (`uvicorn ...`), verify `/health/live` and `/health/ready`.
- Start frontend pointing to backend origin.

## Handling Model Load Failure
- Symptom: `/health/ready` returns 503 with model load error.
- Steps:
  - Check `MODEL_PATH` exists and readable; confirm hash matches expected.
  - Validate device availability if using `cuda`; fall back to `cpu` if unavailable.
  - Restart service after correcting path/hash/device.

## Investigating High Move Latency
- Check metrics for move and inference latency (p95).
- Inspect logs for validation errors or inference failures.
- Verify model size and device selection; switch to deterministic/stubbed agent for debugging.
- Run load test locally to reproduce; profile hot paths.

## Game State Issues (desync/duplicates)
- Confirm server rejects duplicates and finished games (API returns 400/409).
- Inspect move history for given `game_id`.
- If state is corrupted, end the game and start a new one; monitor for recurring patterns.
