# Functional Requirements (Derived from BRs)

## FR-001 Gameplay API
- Parent BR: BR-001
- Requirement Statement: Provide REST endpoints to start a game, submit moves, and quit, enforcing Battleship rules and validation.
- Detailed Specification: `/api/games` POST creates game, returns game_id + initial state; `/api/games/{id}/moves` POST validates bounds/duplicates/status, updates state, returns player + RL agent moves; `/api/games/{id}/quit` POST ends session and frees state; structured errors (400/404/409/429/503).
- Acceptance Criteria: API contract per API_SPEC; rejects invalid/duplicate/out-of-bounds; finished games reject moves; readiness tied to model load.
- Constraints: stateless API instances; in-memory state for MVP; masked boards for client.
- Traceability: BR-001; linked User Stories US-001/US-002/US-003/US-004; NFRs (latency, reliability, security/validation).

## FR-002 RL Agent Move Generation
- Parent BR: BR-001
- Requirement Statement: Generate RL agent moves per turn using a deterministic stub in tests and real model in runtime.
- Detailed Specification: In-process agent adapter; deterministic/stubbed mode for tests via flag/seed; real model uses configured artifact and device; errors surface as 503 and mark game aborted.
- Acceptance Criteria: deterministic outputs in test mode; real mode returns valid coordinates/outcomes; errors logged and surfaced; readiness reflects model load.
- Constraints: respect MODEL_PATH/HASH/DEVICE; no on-the-fly training in runtime.
- Traceability: BR-001; US-003/US-004; NFRs (latency, reliability).

## FR-003 Frontend Play Loop
- Parent BR: BR-001
- Requirement Statement: Provide a web UI to start a game, display boards, submit moves, show RL responses, and quit with clear states/errors.
- Detailed Specification: Homepage CTA to start; board rendering; move submission with feedback; displays agent move; handles 400/404/409/429/503 gracefully; shows readiness/health status; responsive layout.
- Acceptance Criteria: start/play/quit flows exercised; error states surfaced; tests cover happy/error flows.
- Constraints: anonymous; no persistence/auth.
- Traceability: BR-001; US-001..US-004; NFRs (usability, performance).

## FR-004 Deployment Readiness
- Parent BR: BR-002
- Requirement Statement: Deliver containerized services with health/readiness endpoints and k8s-ready manifests/overlays for dev/test/prod, plus separate training env.
- Detailed Specification: Dockerfiles for backend/frontend; readiness ties to model load/hash; k8s manifests/overlays include liveness/readiness probes; training namespace isolated; local compose/devcontainer for local-first.
- Acceptance Criteria: containers build; probes pass locally; manifests validate; training isolated from runtime.
- Constraints: open-source only; no paid cloud without approval.
- Traceability: BR-002; NFRs (operations, availability, security); ADRs for stack/runtime.

## FR-005 Cost Guardrails
- Parent BR: BR-003
- Requirement Statement: Enforce cost guardrails (no paid SaaS/cloud) and require ADR for any cost-incurring proposal.
- Detailed Specification: Document allowed/disallowed services; guardrails in CONFIGURATION/PROJECT_POLICY; ADR flow for exceptions; CI checks avoid paid services; deployment docs avoid paid infra.
- Acceptance Criteria: zero paid dependencies; ADR exists for any exception; configs/docs reflect guardrails.
- Constraints: cost-incurring changes need supervisor approval.
- Traceability: BR-003; NFRs (compliance/cost); ADRs for any exceptions.

## FR-006 Observability & Quality Gates
- Parent BR: BR-004
- Requirement Statement: Instrument gameplay/inference/readiness with metrics/logs/traces and enforce quality gates (coverage/CI) per TEST_STRATEGY/OBSERVABILITY_SPEC.
- Detailed Specification: metrics for start/move/quit/inference; structured logs with game_id/model metadata; traces where enabled; coverage targets enforced; load/perf baseline for move latency; readiness tied to model load.
- Acceptance Criteria: signals emitted per OBSERVABILITY_SPEC; coverage targets met; load/perf targets recorded; health/readiness endpoints wired.
- Constraints: no sensitive data in logs; no secrets; deterministic tests.
- Traceability: BR-004; NFRs (performance, reliability, observability, security).
