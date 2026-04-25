# Non-Functional Requirements (Derived from BRs)

## NFR-001 Performance & Latency
- Parent BR: BR-004
- Category: performance
- Requirement Statement: Gameplay move handling (player + agent) should meet p95 latency targets suitable for interactive play; readiness checks must respond promptly.
- Metrics / Thresholds: move endpoint p95 ≤ 500ms (dev baseline); inference p95 ≤ 200ms; readiness success ≥ 99%.
- Scope / Components Affected: backend API, agent adapter, frontend UX for latency/error surfacing.
- Linked FRs / Features: FR-001, FR-002, FR-003, FR-006.

## NFR-002 Reliability & Availability
- Parent BR: BR-004
- Category: reliability
- Requirement Statement: Core gameplay flows (start/move/quit) and readiness must maintain high success rates; failures should be detectable and recoverable.
- Metrics / Thresholds: gameplay success rate ≥ 99% (excluding client errors) in normal ops; readiness success ≥ 99%.
- Scope / Components Affected: API, agent adapter, health/readiness.
- Linked FRs / Features: FR-001, FR-002, FR-006.

## NFR-003 Observability & Auditability
- Parent BR: BR-004
- Category: observability
- Requirement Statement: Emit metrics/logs/traces for start/move/quit/inference with sufficient context to debug issues without sensitive data.
- Metrics / Thresholds: metrics coverage per OBSERVABILITY_SPEC; structured logs with game_id and model metadata; traces on main flows.
- Scope / Components Affected: API handlers, agent adapter, health/readiness, CI.
- Linked FRs / Features: FR-001, FR-002, FR-006.

## NFR-004 Security & Validation
- Parent BR: BR-004
- Category: security
- Requirement Statement: Enforce strict input validation for gameplay; protect against leaking sensitive info; guard model paths/hashes; no secrets in logs.
- Metrics / Thresholds: validation error handling rate monitored; zero secrets/PII in logs; hash verification on model load.
- Scope / Components Affected: API validation, agent adapter, logging.
- Linked FRs / Features: FR-001, FR-002, FR-006.

## NFR-005 Cost & Compliance
- Parent BR: BR-003
- Category: compliance
- Requirement Statement: Avoid paid SaaS/cloud; document and enforce cost guardrails; require ADRs for exceptions.
- Metrics / Thresholds: zero paid services in dependency scans/configs; ADR + approval for any cost-incurring proposal.
- Scope / Components Affected: infra/config, deployment choices, dependencies.
- Linked FRs / Features: FR-004, FR-005.

## NFR-006 Operations & Deployment Readiness
- Parent BR: BR-002
- Category: operations
- Requirement Statement: Containerized services with health/readiness probes; k8s manifests/overlays validated; training isolated from runtime envs.
- Metrics / Thresholds: successful container builds; probes pass; manifests lint/validate; isolation between runtime/training.
- Scope / Components Affected: deployment configs, health/readiness, training pipeline.
- Linked FRs / Features: FR-004, FR-006.
