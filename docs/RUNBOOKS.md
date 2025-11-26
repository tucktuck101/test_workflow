# Runbooks

## Model Artifact Promotion (FEAT-006)
- Preconditions:
  - Candidate artifact + `manifest.json` (hash/version/device/seed/board) produced by training.
  - Validation: `python -m tools.validate_artifact --artifact <path> --manifest <path> --root <allowed_root> --device <cpu|cuda>` must return status ok.
- Steps:
  1. Copy artifact + manifest into runtime artifact store (or image layer) under allowed root.
  2. Update runtime config/env (`MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE`, `MODEL_ROOT`) to point to candidate.
  3. Deploy/update backend; wait for `/health/ready` to report ready with new version/hash.
  4. Watch dashboards: readiness (model_ready), move latency p95, inference error rate, active games.
  5. Announce promotion complete; note version/hash in CHANGELOG/EPIC_LOG if required.
- Alerts/monitoring:
  - Fast burn: inference error rate >1% (5m); move p95 >500ms (15m slow burn).
  - Readiness failing >2m blocks rollout; investigate hash/path/device mismatch.
  - Capacity nearing cap: active_games >90% of `MAX_ACTIVE_GAMES` (warn).

## Model Artifact Rollback
- Trigger: readiness fails after promotion or elevated error/latency beyond budget.
- Steps:
  1. Pin back to N-1 manifest: set `MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, `MODEL_DEVICE` to previous values (config/ConfigMap/env).
  2. Deploy/update backend; verify `/health/ready` returns ready with N-1 version/hash.
  3. Monitor dashboards/alerts for stability (readiness, move/inference latency/error).
  4. Record rollback in EPIC_LOG and create follow-up issue for failed artifact.
- Readiness failure handling:
  - If validation fails (hash/path/device), stop traffic until rollback applied.
  - Keep N-1 artifact/manifest available at all times for fast rollback.
