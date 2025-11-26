# Software Design Review — Battleship RL MVP

## 1. Executive Summary
- Build a production-ready, anonymous Battleship web app where players face a pre-trained RL agent. Local-first with clear path to Kubernetes for dev/test/prod, plus an isolated training environment. Open-source stack (React/TypeScript frontend, FastAPI/Python backend, PyTorch RL).
- Architecture couples the gameplay API and in-process RL inference for low latency, served via REST to a browser SPA. Model artifacts are versioned, hash-verified, path-validated, and loaded at startup; readiness blocks traffic until safe. Training remains offline/separate; no live training in runtime.
- Key decisions: monorepo; in-memory session state for MVP with `MAX_ACTIVE_GAMES` cap; deterministic/stubbed inference mode for tests; cost guardrail of zero paid SaaS/cloud until explicitly approved; strong observability (metrics/logs/traces) on start/move/quit/inference/readiness.
- Major risks: inference/turn latency under load; model integrity or missing artifact; DoS via game creation/moves; test flakiness without determinism; operational gaps when introducing persistence later; model quality/fun factor. Recommendations: enforce readiness/hash checks, load/perf test move + inference paths, add basic rate limits/backoff handling, keep ADRs for persistence and any cost-incurring changes, and iterate on model quality.

## 2. System Context & Problem Definition
- **Primary users/personas:**  
  - Anonymous players: want frictionless start/play/quit against an RL agent.  
  - Operators/SRE/DevOps: need health/readiness, observability, safe deploy/rollback.  
  - RL engineers: train and publish model artifacts; ensure integrity and performance.
- **External systems/dependencies:** browser clients; model artifact storage (local path/volume); CI/CD; Kubernetes (future); PyTorch runtime; observability stack (OSS).
- **Problem statement:** Deliver an engaging Battleship experience versus an RL opponent with low-latency turns, high reliability, and zero-auth friction while remaining cost-neutral and deployment-ready.
- **Success criteria:** p95 move latency ≤500ms (dev baseline); gameplay success ≥99%; readiness ≥99%; zero paid services; containerized and k8s-ready; observability per spec.
- **Assumptions & constraints:** anonymous MVP (no auth/persistence); in-memory state acceptable; open-source only; no paid cloud/SaaS; environments dev/test/prod + isolated training; CPU default, GPU optional; deterministic mode for tests; path validation restricts model artifacts to an allowed root.
- **Out of scope (MVP):** accounts/leaderboards/history; paid cloud/SaaS; live training in runtime; advanced rate limiting/throttling (planned); persistence of game history.
- **System context (C4 L1, prose):** A public browser SPA (players) calls a RESTful Gameplay API. The API contains the game engine and in-process RL inference. It reads a local/volume-mounted model artifact. Operators observe via metrics/logging/tracing and health/readiness probes. Training pipeline (separate env) produces artifacts consumed by runtime.
- **External dependencies summary:**

| Name | Type | Purpose | Criticality | Notes |
| --- | --- | --- | --- | --- |
| Browser SPA | Client | Player UI, calls API | High | Anonymous; handles error codes gracefully |
| Model Artifact Store (fs/volume) | Storage | Provide versioned RL model | High | Hash-verified at startup |
| PyTorch Runtime | Library | Inference/training | High | CPU default; GPU when available |
| CI/CD (GitHub Actions or equivalent) | Pipeline | Build/test/lint/scan | High | Enforces quality gates |
| Kubernetes (future) | Platform | Deploy dev/test/prod | Medium | Readiness/liveness probes |
| Observability Stack (Prometheus/Grafana/Loki/Tempo, OSS) | Tooling | Metrics/logs/traces | Medium | Can run locally/self-hosted |

## 3. Functional Design Requirements
- **FR-001 Gameplay API** — REST endpoints for start/move/quit enforcing Battleship rules and validation.  
  - Acceptance: contracts per `docs/API_SPEC.md`; rejects invalid/duplicate/out-of-bounds; finished games reject moves; readiness tied to model load.
- **FR-002 RL Agent Move Generation** — In-process RL agent with deterministic stub for tests.  
  - Acceptance: deterministic outputs in test mode; real mode returns valid coords/outcomes; inference errors → 503 + cleanup; readiness reflects model load.
- **FR-003 Frontend Play Loop** — Web UI to start game, submit moves, show agent responses, quit with clear states/errors.  
  - Acceptance: start/play/quit exercised; error states surfaced for 400/404/409/429/503; responsive layout.
- **FR-004 Deployment Readiness** — Containerized frontend/backend; health/readiness endpoints; k8s-ready manifests/overlays; separate training env.  
  - Acceptance: images build; probes pass; manifests validate; training isolated.
- **FR-005 Cost Guardrails** — Enforce no paid SaaS/cloud; ADR for exceptions.  
  - Acceptance: zero paid dependencies; ADR exists for any exception; configs/docs reflect guardrails.
- **FR-006 Observability & Quality Gates** — Metrics/logs/traces for start/move/quit/inference/readiness; CI coverage and scans per TEST_STRATEGY/OBSERVABILITY_SPEC.  
  - Acceptance: signals emitted per spec; coverage targets met; load/perf baseline recorded; health/readiness wired.

**Example user stories (major capabilities):**
- As a player, I want to start a new game so that I can play against the RL agent (US-001).
- As a player, I want to submit moves and see hit/miss/sunk plus the agent’s response so that I can progress the game (US-002/US-003).
- As a player, I want to quit early so that no lingering state remains (US-004).
- As an operator, I want to check health/readiness so that I know the service and model are ready (US-005).

**Traceability (overview):**

| Requirement ID | Related SLO/SLI | Verification (Test/Check) |
| --- | --- | --- |
| FR-001, FR-002, FR-003 | Latency (move), Availability | API/Integration tests, Load tests, CI contract tests |
| FR-004 | Readiness SLI, Availability | Smoke tests, Probe validation, CI startup checks |
| FR-006 | Latency, Error Rate, Readiness | Observability unit/integration tests, CI coverage gates |
| NFR-PERF-01/02 | Latency (move/inference) | Load tests (k6/Locust), perf CI job (optional) |
| NFR-REL-01/02 | Availability, Readiness | SLO monitors, burn-rate alerts |
| NFR-SEC-01/02/03 | Error Rate, Compliance | Schema validation tests, dependency/secrets scans |
| NFR-MAINT-01 | n/a (quality) | Coverage gates in CI |
| NFR-OBS-01/02/03 | Observability SLIs | Instrumentation tests, dashboard/alert checks |

## 4. Non-Functional Requirements (NFRs)
- **Reliability / Availability**  
  - NFR-REL-01: Gameplay start/move/quit success rate ≥99% (excluding 4xx) over rolling 1h.  
  - NFR-REL-02: Readiness success ≥99% over rolling 1h; error budget = 1% of minutes per 30-day window.
- **Performance**  
  - NFR-PERF-01: `/api/games/{id}/moves` p95 latency ≤500ms (dev baseline); tighten post-load test.  
  - NFR-PERF-02: RL inference p95 latency ≤200ms.  
  - NFR-PERF-03: Readiness endpoint responds ≤200ms in steady state.
- **Scalability**  
  - NFR-SCAL-01: Support at least 200 concurrent active games in dev baseline; scale horizontally by backend replicas with shared nothing (session state in-memory per pod; stickiness or gateway routing required if sharded).  
  - NFR-SCAL-02: Autoscale on move latency and active games metrics (future k8s HPA).
- **Security**  
  - NFR-SEC-01: Strict input validation; reject payloads >1KB; return structured error codes only.  
  - NFR-SEC-02: Model artifact hash verification and path allowlist mandatory; readiness fails on mismatch or invalid path.  
  - NFR-SEC-03: No secrets/PII in logs; dependency & secrets scanning on every PR.
- **Maintainability / Operability**  
  - NFR-MAINT-01: Code coverage targets—engine ≥90%, backend 85–90%, frontend 70–80%; no >2pp drop per component without justification.  
  - NFR-MAINT-02: Runbooks for start/move/quit/inference failures; ADRs for architectural changes (persistence, cost exceptions).  
  - NFR-MAINT-03: Configuration via env; fail fast on missing/invalid config.
- **Usability**  
  - NFR-USE-01: UI renders in <2s on baseline hardware; errors mapped to friendly messages for 400/404/409/429/503.  
  - NFR-USE-02: Responsive layout for desktop/mobile.
- **Observability**  
  - NFR-OBS-01: Emit metrics/logs/traces for start/move/quit/inference/readiness with `game_id` correlation; model_version/device tags.  
  - NFR-OBS-02: Dashboards for latency, success, readiness, inference errors; alerts when SLOs breached.  
  - NFR-OBS-03: Trace sampling configurable; deterministic traces in tests.
- **Compliance / Cost**  
  - NFR-COMP-01: Zero paid SaaS/cloud during MVP; ADR required for exceptions.  
  - NFR-COMP-02: Align with OWASP ASVS input validation; ISO/IEC 25010 quality attributes documented.  
  - NFR-COMP-03: Artifact promotion includes version/hash metadata; audit trail of model versions.

## 5. Architecture Overview
- **Style:** Two-service web app (SPA + REST API) with in-process RL inference; monorepo. Chosen to minimize latency, simplify deployment, and suit local-first development with k8s readiness.
- **C4 L2 (prose):**  
  - Container: Browser SPA (React) communicates via HTTPS/REST to Backend API (FastAPI).  
  - Container: Backend hosts API layer, game engine, session store (in-memory), agent adapter (PyTorch inference), observability layer.  
  - External: Model artifact store (local/volume). Training pipeline (separate job/env) outputs artifacts consumed by backend. Observability stack receives metrics/logs/traces.
- **Data flow:** Player starts game → backend creates session, seeds boards → returns `game_id` + masked board. Player submits move → backend validates, updates board, calls in-process inference for agent move → returns outcomes/status. Quit ends session and frees memory. Health/readiness expose process/model state.
- **Fault tolerance & resilience:** Readiness gated on model load/hash/path; inference failures abort game and return 503; `MAX_ACTIVE_GAMES` cap; planned rate limiting/backoff; stateless pods aside from in-memory sessions (requires sticky routing or single-replica in MVP). Rollback by reverting model version/hash and redeploying.
- **Capacity guardrails:** Start with `MAX_ACTIVE_GAMES` aligned to the 200-concurrency target; tune based on memory profile per pod from load tests. Document cap changes and ensure alerts on >90% utilization.
- **Isolation boundaries:** Anonymous play; no user data persistence. Training isolated from runtime. Model artifacts read-only. Future multi-tenant concerns minimal in MVP.
- **Networking:** Public API via HTTPS; CORS restricted to frontend origin; health endpoints internal. k8s: backend in private namespace; service fronted by ingress; readiness/liveness probes.
- **Main components summary:**

| Component | Responsibility | Tech Stack | Scaling | Notes |
| --- | --- | --- | --- | --- |
| Frontend SPA | UI for start/play/quit, error handling | React + TypeScript (Vite) | Static assets via CDN/ingress | Anonymous; maps API errors to UX |
| Backend API & Engine | REST endpoints, rules, validation, session mgmt | Python + FastAPI | Horizontal; session stickiness needed | In-process inference; readiness/health |
| Agent Adapter | Load model, deterministic stub, inference call | PyTorch | Shares backend scale | CPU default; GPU optional |
| Training Pipeline | Offline training to produce artifacts | PyTorch jobs | Batch; isolated env | Outputs versioned artifact + hash |
| Observability Layer | Metrics/logs/traces export | OpenTelemetry + OSS stack | N/A | Structured logs, low cardinality |

## 6. Detailed Component Design
- **C1 Frontend SPA**  
  - Responsibility: Render homepage/boards; call start/move/quit; display agent moves/errors; show readiness status.  
  - Interfaces: REST to `/api/games`, `/api/games/{id}/moves`, `/api/games/{id}/quit`, `/health/ready`.  
  - Data: Holds transient game state from API responses; no persistence.  
  - Error handling: Map 400/404/409/429/503 to UX messages with retry/backoff hints.  
  - Dependencies: Backend API; CORS config; build tooling.  
  - Limitations: Offline use not supported; depends on backend latency.
- **C2 Backend API Layer (FastAPI)**  
  - Responsibility: Routing, validation, response shaping, HTTP status codes; exposes health/live/ready.  
  - Interfaces: Incoming REST; calls Game Engine, Session Store, Agent Adapter.  
  - Data: Validates payloads (<1KB), coordinates, game state; returns structured errors.  
  - Error handling: 400 invalid/duplicate; 404 not found; 409 finished; 429 cap; 503 inference/model not ready.  
  - Dependencies: Game Engine, Session Store, Agent Adapter, Observability Layer.  
  - Limitations: Stateful per pod (in-memory).
- **C3 Game Engine**  
  - Responsibility: Board setup, ship placement, move adjudication, status transitions, deterministic seeding.  
  - Interfaces: Called by API layer; returns outcomes and updated state.  
  - Data models: As per `docs/DATA_MODEL.md` (`game_id`, boards, ships, move_history, status).  
  - Error handling: Reject out-of-bounds/duplicate/finished; marks aborted on inference failure.  
  - Dependencies: Session Store; Agent Adapter (for agent move).  
  - Known risks: RNG determinism must be enforced in tests; memory growth bounded by `MAX_ACTIVE_GAMES`.
- **C4 Session Store (in-memory)**  
  - Responsibility: Store active games keyed by `game_id`; TTL/cleanup on quit/end/timeout.  
  - Interfaces: CRUD by Game Engine/API.  
  - Data: Game sessions; TTL metadata.  
  - Error handling: Returns not-found; rejects finished.  
  - Dependencies: None external.  
  - Limitations: Loss on restart; sticky routing or single-replica needed.
- **C5 Agent Adapter (PyTorch in-process)**  
  - Responsibility: Load model from `MODEL_PATH`; verify `MODEL_HASH`; choose `MODEL_DEVICE`; provide deterministic stub when configured; return agent move.  
  - Interfaces: Called from Game Engine; exposes `infer(game_state)` returning coordinates/outcome; exposes load status for readiness.  
  - Error handling: On load/hash/device errors → readiness 503; on inference errors → raise and mark game aborted with 503.  
  - Dependencies: File system/volume for artifacts; PyTorch runtime; config envs.  
  - Limitations: Tied to backend process; GPU availability varies; model quality affects fun/playability.
- **C6 Observability & Config Layer**  
  - Responsibility: Structured logging, metrics, tracing; env parsing/validation.  
  - Interfaces: Exposes counters/histograms/gauges; trace spans for start/move/quit/inference; logging hooks.  
  - Data: `game_id`, model metadata, statuses; avoids payloads.  
  - Error handling: Fails fast on invalid config; readiness fails if observability critical path misconfigured (optional).  
  - Dependencies: OpenTelemetry SDK/exporters; stdout for logs.  
  - Limitations: Sampling must avoid high cardinality; ensure defaults for local dev.
- **C7 Training Pipeline (separate env)**  
  - Responsibility: Train RL model; emit artifact + manifest (version/hash/device, hyperparams, timestamp).  
  - Interfaces: Outputs to artifact store; manual/automated promotion into runtime.  
  - Data: Model weights, metadata.  
  - Error handling: Training failures isolated; do not affect runtime.  
  - Dependencies: Compute (CPU/GPU), datasets.  
  - Limitations: Out of runtime scope; promotion must be manual/controlled for MVP.

### RL Training Design (planned, FEAT-007)
- **Environment:** Battleship board size configurable (default 10); observation is player/agent boards with hit/miss/sunk markers; action space = grid coordinates; episode ends on win/lose/quit; reward: positive for hit/sunk/win, small penalty per move to encourage efficiency.
- **Baseline opponent:** Random/heuristic opponent for training/eval; deterministic seed support for tests.
- **Model/Algorithm:** PyTorch policy/value network (e.g., small CNN/MLP on board grids). Start with CPU-first, optional CUDA flag. Algorithm: simple policy gradient (REINFORCE or DQN variant) to keep compute bounded.
- **Training recipe:** Configurable episodes, LR, batch sizes. Two configs: mini-train for CI (tens of episodes, seconds to run, deterministic hash) and full-train for local/manual runs (documented, not in CI). Seeded for reproducibility.
- **Evaluation:** Harness to play N games vs random/heuristic; report win rate and average moves. Sanity check: model must beat random by a margin; mini-train may just verify convergence directionally.
- **Artifacts:** Emit weights file + `manifest.json` (version/hash/device/seed/board_size/hparams). Compatible with runtime validator/promotion flow.
- **Guardrails:** CPU-only by default; no paid cloud/GPU without ADR; deterministic mini-train required for CI smoke.

**Example flow (move):** Player `POST /api/games/{id}/moves` → API validates payload/state → Game Engine updates player board → Agent Adapter called (real or deterministic stub) → agent move returned → Game Engine updates agent board/status → Observability emits metrics/logs/traces → 200 response with outcomes/masked boards; errors handled per above.

## 7. Integration Design
| ID | Name | Direction | Protocol/Data | AuthZ/AuthN | Versioning | Failure Behaviour |
| --- | --- | --- | --- | --- | --- | --- |
| INT-01 Browser ↔ Backend API | Inbound to backend | HTTPS REST + JSON | None (anonymous) | URL path/semantic; payload schemas in API_SPEC | 400/404/409/429/503 with structured error codes; retries with backoff on 429/503 |
| INT-02 Backend ↔ Model Artifact Store (fs/volume) | Outbound read | File IO; hash check | Path allowlist; no credentials for local | Manifest version/hash; env-driven path | Fail fast on missing/hash mismatch; readiness=503; do not serve traffic |
| INT-03 Backend ↔ PyTorch Runtime | In-process | Python API / torch | N/A | Library version pinned in env/lockfile | On inference error, abort game and return 503; consider circuit-breaker if repeated |
| INT-04 Backend ↔ Observability Stack | Outbound | OTLP/HTTP or gRPC; logs stdout | Access via service account when remote (future) | Metrics/trace schema versioned via exporters | Buffer/drop on exporter failure; do not block request path |
| INT-05 Training Pipeline → Artifact Store | Outbound write | File/object write with manifest | TBD (local write; future signed uploads) | Semantic/timestamped model versions | Mark artifact with hash; promotion manual; rollback by reverting manifest |

- **Backwards compatibility:** API changes require versioned endpoints or additive-only changes; contract tests guard stability. Breaking changes require `/v2` and parallel support during migration. Model artifacts use semantic/timestamped versions plus hash; runtime serves a single active version.
- **Breaking changes handling:** Use ADR + migration plan; dual-write/dual-read for future persistence; for API, introduce `/v2` when needed.

## 8. Observability & Telemetry Plan
- **SLIs/SLOs:**

| SLI | Description / Formula | SLO Target |
| --- | --- | --- |
| Availability (gameplay) | `successful_game_requests / total_game_requests` (2xx only) over 1h | ≥99% |
| Latency (move) | p95 of `/api/games/{id}/moves` end-to-end | ≤500ms (dev baseline) |
| Error Rate (inference) | `inference_errors / inference_calls` | <1% |
| Readiness | `ready_responses / readiness_checks` | ≥99% |
| Saturation | CPU/memory utilization on backend pods; active games gauge | <70% CPU, <75% memory sustained |

- **Metrics:** Request counts/latency (start/move/quit); inference latency/errors; validation errors by code; active games; game outcomes; readiness gauge with model_version/hash/device labels.  
- **Logging:** Structured JSON or key-value; fields: timestamp, level, endpoint, status, `game_id`, outcome, model_version, error_code. Exclude payloads/coordinates/secrets. Correlate with trace/span IDs. Retain logs 7–14 days in MVP with rotation; no payloads/PII ever stored.  
- **Tracing:** OpenTelemetry; spans `game.start`, `game.move`, child `inference.call`, `game.quit`; attributes: `game_id`, model_version, device, status/outcome; sampling configurable (tests = always on).  
- **Dashboards (initial):**  
  - Player experience: turn latency/success, game outcomes.  
  - Ops: readiness status with version/hash, inference latency/error rate, active games & outcomes, resource utilization, restarts.  
- **Alerts (burn-rate style):**  
  - Fast burn: availability <99% over 5m or readiness failing >2m → page/block release.  
  - Slow burn: availability <99% over 1h or readiness <99% over 1h → ticket/investigate.  
  - Latency: move p95 >500ms for 5m; inference error rate >1% for 5m.  
  - Capacity: active games >90% of `MAX_ACTIVE_GAMES` for 10m.  
- **Error budget policy:** Pause releases when budget exhausted; require RCAs for burn >25% in a day; re-enable after mitigations verified.  
- **Tools:** OpenTelemetry SDK; Prometheus/Grafana/Loki/Tempo (self-hosted/local); CI logs for smoke metrics.  
- **Runbooks:** Model load failure, high move latency, and state issues covered in `docs/RUNBOOKS.md`.

## 9. Testing Strategy
- **Levels & scope:**  
  - Unit: rule validation, board logic, inference adapter (stubbed), config parsing.  
  - Integration/API: start/move/quit incl. error codes; model load paths; in-memory lifecycle.  
  - Contract: API_SPEC validation against frontend/client tests.  
  - E2E/UI: start/play/quit flows in browser test harness.  
  - Performance/Load: move/start under concurrency (k6/Locust).  
  - Security: dependency/secrets scanning; basic SAST.
- **Ownership:** Backend/engine unit/API by backend devs; frontend by frontend devs; load by performance lead; security scans automated in CI.  
- **Coverage expectations:** Engine ≥90%; backend 85–90%; frontend 70–80%; no >2pp drop on touched components without justification.  
- **CI integration:**  
  - Pre-merge: lint/format, type checks (mypy/tsc), unit + API/contract tests, coverage thresholds enforced, dependency/secrets scans, readiness/model smoke in deterministic mode.  
  - Nightly/on-demand: load/perf tests, E2E/UI runs, extended property-based tests (if added). Deterministic mode off for GPU/real-model path when available.  
- **Test matrix:**

| Test Type | Scope | Trigger | Tools | Exit Criteria |
| --- | --- | --- | --- | --- |
| Unit | Engine, adapter, config | On commit/PR | pytest, fastapi deps, ts/vitest | Pass/fail; coverage per target |
| API/Integration | REST flows, model load, session lifecycle | On PR | pytest/httpx, docker-compose | Contracts met; no regressions |
| Contract | API schema vs client | On PR/nightly | schemathesis/PACT (optional) | No breaking changes |
| E2E/UI | Start/play/quit UX | Nightly/on-demand | Playwright/Cypress | Key flows pass; screenshots diffs ok |
| Load/Perf | Move/start under load | Nightly/on-demand | k6/Locust | p95 latency within budget; no errors |
| Security/Quality | Deps/secrets/SAST | On PR | pip-audit/npm audit, gitleaks | No critical/high vulns; no secrets |

## 10. Deployment & CI/CD Strategy
- **Environments:** Local dev; dev/test/prod runtime namespaces; isolated training env. Local-first until cloud approved.  
- **Deployment approach:** Container images for frontend/backend; k8s readiness/liveness probes; rolling deploys for MVP; shift to canary when multi-replica and stickiness are available. Single backend replica or sticky sessions until state externalized; future HPA.  
- **Pipeline gates:** lint/format → type checks → unit/integration/contract tests → coverage check → dependency/secrets scans → build images → smoke (readiness/model load in deterministic mode).  
- **IaC & config:** K8s manifests/overlays (kustomize/Helm TBD) with ConfigMaps for non-secret envs; Secrets reserved for future sensitive data; Dockerfiles per service. Model artifacts packaged in image or mounted read-only volume with manifest.  
- **Secrets management:** None for MVP; future via k8s Secrets/Sealed Secrets; never commit secrets.  
- **Rollback & DR:** Keep previous model artifact version/hash; rollback by updating env/config and redeploying; readiness blocks traffic until hash verified. In-memory state means stateless rollback; accepted risk of game loss. DR: redeploy from images + artifact store. Target RTO: minutes; RPO: accepted loss of in-flight games (in-memory only).  
- **Release criteria:** SLO adherence in staging; readiness green; observability hooks verified; ADRs up to date.

## 11. Risk Assessment & Mitigation
| ID | Description | Category | Likelihood | Impact | Risk Level | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | Inference latency too high for interactive play | Performance | Medium | High | High | Keep inference in-process; optimize model; monitor p95; load test; allow lighter policy | Backend |
| R-02 | Model artifact missing/corrupted | Operational | Low | High | Medium | Hash verification; path allowlist; fail readiness; keep N-1 artifacts; promotion checklist | Backend |
| R-03 | DoS via game creation/move spam | Security/Operational | Medium | Medium | Medium | `MAX_ACTIVE_GAMES` cap; add rate limits/backoff; monitor active games | Backend |
| R-04 | State loss on restart (in-memory) | Operational | Medium | Low | Low | Accepted for MVP; plan persistence ADR; communicate expected behavior | Backend |
| R-05 | Determinism gaps cause flaky tests | Quality | Low | Medium | Low | Deterministic mode/stub; seed RNG; fixtures for boards | QA |
| R-06 | Observability gaps hide failures | Reliability | Low | High | Medium | Enforce OBSERVABILITY_SPEC; CI smoke with readiness/model checks; dashboards/alerts | SRE |
| R-07 | GPU/CPU divergence across envs | Technical | Medium | Medium | Medium | Default to CPU; guard device config; optional GPU node selectors; test both paths when available | Backend/RL |
| R-08 | Model quality insufficient for fun gameplay | Product/Technical | Medium | Medium | Medium | Iterate training; evaluation loop; allow swapping artifacts via config; gather feedback | RL |
| R-09 | Load under concurrency (move endpoint) | Performance | Medium | High | High | Load test; cap active games; optimize validation paths; consider autoscale triggers | Backend |

Top risks requiring active management: R-01 (latency), R-02 (artifact integrity), R-03 (DoS), R-06 (observability gaps), R-09 (concurrency load).

## 12. Compliance & Standards Mapping
- **ISO/IEC 25010 (quality attributes):** NFRs cover performance, reliability, security, maintainability, usability, compatibility (API contracts), portability (containers/k8s).  
- **ISO/IEC 42010 (architecture description):** This SDR provides stakeholders, context, views (C4 prose), decisions (ADRs), and rationale.  
- **ISO/IEC 15289 (software documentation):** Requirements (FR/NFR), architecture, design, test, deployment, and compliance sections documented for traceability.  
- **OWASP ASVS alignment:** Input validation (bounds/payload size/state), error handling without leakage, dependency/secrets scanning in CI, path allowlist + hash verification for artifacts, planned rate limiting/backoff guidance, logs without secrets/PII.  
- **SRE practices:** SLIs/SLOs with error budgets; alerting/dashboards; readiness/liveness; rollback strategies.  
- **Cost/compliance guardrails:** Zero paid SaaS/cloud during MVP; ADR for exceptions; aligns with repository PROJECT_POLICY.

## 13. Appendices & Supporting Material
- **Glossary:** `game_id` (UUID session key); `model_version` (artifact identifier); `MODEL_HASH` (SHA256); `DETERMINISTIC_MODE` (flag for stubbed/seeded inference); `MAX_ACTIVE_GAMES` (soft cap).  
- **Data dictionary:** See `docs/DATA_MODEL.md` for session fields (`player_board`, `agent_board_masked/full`, `ships`, `move_history`, `status`, timestamps, deterministic_seed).  
- **ADR summary:** ADR-0002 selects React/TS + FastAPI + PyTorch with in-process inference; ADR-0003 defines in-memory state, hash-verified artifacts, deterministic mode; ADR-0001 sets workflow/tier (standard).  
- **Runbooks:** See `docs/RUNBOOKS.md` for startup/deployment checklist, handling model load failures, investigating high move latency, and addressing game state issues.  
- **Prototype/spikes:** None implemented yet.  
- **Diagrams:**  
  - Start/Move/Quit sequence (mermaid):
    ```mermaid
    sequenceDiagram
      participant Player
      participant Browser
      participant Backend as Backend (FastAPI)
      participant Store as Session Store (in-memory)
      participant Agent as Agent Adapter (PyTorch)

      Player->>Browser: Click "Start"
      Browser->>Backend: POST /api/games
      Backend->>Store: Create session (boards, seed)
      Store-->>Backend: Session created (game_id)
      Backend-->>Browser: 200 game_id, boards, status

      Player->>Browser: Submit move
      Browser->>Backend: POST /api/games/{id}/moves (x,y)
      Backend->>Store: Validate game/state/bounds/dupes
      Store-->>Backend: State OK
      Backend->>Agent: infer(game_state) (deterministic or real)
      Agent-->>Backend: Agent move/outcome
      Backend->>Store: Update boards/status/history
      Backend-->>Browser: 200 player_result, agent_move, status

      Player->>Browser: Quit game
      Browser->>Backend: POST /api/games/{id}/quit
      Backend->>Store: End session, free memory
      Store-->>Backend: Session ended
      Backend-->>Browser: 200 status=ended
    ```

  - Deployment (k8s, probes/ingress/stickiness):
    ```mermaid
    flowchart LR
      Player[Player Browser] -->|HTTPS| Ingress[Ingress/HTTPS]
      Ingress --> SPA[SPA Assets (Static/CDN)]
      SPA -->|REST /api| BackendSvc[Service /api]
      BackendSvc --> Pod[Backend Pod\nFastAPI + Game Engine + Agent Adapter]
      Pod -->|read-only| ModelVol[(Model Artifact Volume)]
      Pod -->|env| Config[ConfigMap/Env Vars]
      Pod -->|liveness/readiness| Probes[Liveness & Readiness]
      Pod -->|metrics/logs/traces| Obs[Prom/Grafana/Loki/Tempo]
      classDef infra fill:#f5f5f5,stroke:#999;
      class Ingress,BackendSvc,Pod,ModelVol,Config,Probes,Obs infra;
      note right of BackendSvc: Use sticky sessions or single replica until state externalized
    ```

  - Startup and model hash verification:
    ```mermaid
    flowchart TD
      A[Backend start] --> B[Load env/config]
      B --> C[Validate MODEL_PATH within allowlist]
      C --> D[Compute SHA256 of artifact]
      D --> E{Hash matches expected?}
      E -- No --> F[Fail fast\nreadiness=503]
      E -- Yes --> G[Select device cpu/cuda]
      G --> H[Load model into memory]
      H --> I[Set readiness=ready\nexpose version/hash/device]
      F -.-> I
    ```
- **Checklists:** Promotion checklist for model artifacts (hash/version); deploy readiness checklist (probes green, SLOs monitored).
