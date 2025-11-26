# ADR-0003-state-and-model-handling

- Status: Accepted
- Date: 2025-11-26
- Deciders: Supervisor, Codex

## Context
- MVP scope keeps gameplay anonymous with no persistence; rapid iteration is preferred over durability.
- Backend must authoritatively enforce game rules and interact with an RL agent, while remaining local-first and Kubernetes-ready later.
- Deterministic/stubbed inference is required for tests and debugging; production must verify model integrity (hash) before serving.
- Cost guardrails disallow paid/cloud services during MVP; simplicity and zero-cost infra are priorities.

## Decision
1) **State storage (MVP):** keep game/session state in-memory inside the FastAPI service with a soft cap on concurrent games (`MAX_ACTIVE_GAMES`). Sessions end on quit/finish or TTL; restarts drop state. Future persistence (e.g., Postgres) will be introduced via a follow-on ADR when accounts/history/leaderboards are added.

2) **Inference placement:** run RL inference in-process within the backend service to minimize latency. Default device `cpu`; allow `cuda` when available and configured. Provide a deterministic/stubbed agent path (gated by `DETERMINISTIC_MODE` or test fixtures) for tests and local debugging; production mode uses the real model or fails readiness if unavailable.

3) **Model artifacts:** require `MODEL_PATH`, `MODEL_VERSION`, `MODEL_HASH`, and `MODEL_DEVICE`. On startup, validate the path within an allowed root, verify SHA256 before load, and fail fast/readiness if missing or mismatched. Artifacts are packaged via image layer or mounted volume; promotion flow must carry version + hash metadata alongside the artifact.

## Consequences
- **Pros:** simple stack with minimal infra; lowest-latency inference; deterministic test path; clear integrity guarantees for artifacts.
- **Cons:** game state is lost on restart; process memory limits active games; inference and API are coupled (resource contention); GPU availability may diverge across environments.
- **Follow-ups:** add persistence ADR when user accounts/history arrive; document artifact promotion pipeline; ensure observability covers state caps, inference latency/errors, and model load status.***
