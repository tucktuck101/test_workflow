# Business Requirements (Derived from VISION.md)

These BRs are ready to be created as Issues using the Business Requirement template (BR-###). Each BR lists suggested parent Epics and downstream links (FR/US/NFR to be created).

## BR-001 Anonymous RL Battleship Experience
- Business Outcome: Deliver an anonymous, production-ready Battleship experience versus an RL agent with smooth start/play/quit flows.
- Problem Statement: No existing product provides a frictionless, anonymous Battleship experience against an RL opponent.
- Success Metrics / KPIs: session success rate; turn latency within target; user completion rate for games; absence of auth friction.
- Scope In: gameplay start/move/quit, RL opponent responses, client-server sync.
- Scope Out: accounts, leaderboards, persistence (later).
- Constraints: anonymous play only; no auth; RL opponent required; BR must link to Epic(s) for gameplay.
- Parent Epic(s): EPIC-001 MVP Gameplay & RL Opponent.
- Linked Requirements: FRs/USs for gameplay API, RL moves, validation; NFRs for latency, reliability.

## BR-002 Local-First with Kubernetes Readiness
- Business Outcome: Enable local-first development with a clear path to deploy on Kubernetes across dev/test/prod plus a separate training environment.
- Problem Statement: Need a deployable, environment-ready stack without committing to paid cloud.
- Success Metrics / KPIs: successful local run; container images build; readiness/liveness probes pass; manifests/overlays validated.
- Scope In: local dev flow, containerization, health/readiness, k8s readiness basics.
- Scope Out: paid cloud services; production cluster rollout until approved.
- Constraints: open-source only; no paid SaaS/cloud without approval; training isolated from runtime envs.
- Parent Epic(s): EPIC-001 (runtime readiness) and EPIC-002 (training isolation).
- Linked Requirements: FRs/NFRs for deployment/readiness/infra constraints.

## BR-003 Cost-Controlled, Open-Source Stack
- Business Outcome: Avoid paid SaaS/cloud and maintain cost neutrality during MVP.
- Problem Statement: Cost guardrails must be enforced to prevent unapproved spend.
- Success Metrics / KPIs: zero paid services; documented cost guardrail compliance; ADRs for any proposed cost-incurring change.
- Scope In: open-source components; local/k8s-compatible tooling; model artifact handling without paid services.
- Scope Out: paid SaaS/cloud unless explicitly approved.
- Constraints: cost guardrails in PROJECT_POLICY.yaml; ADR required for cost-incurring proposals.
- Parent Epic(s): EPIC-001, EPIC-002 (applies across).
- Linked Requirements: NFRs for cost/compliance; ADRs for any exceptions.

## BR-004 Observability, Quality, and Reliability
- Business Outcome: Ensure gameplay, RL inference, and readiness are observable and reliable with strong test coverage.
- Problem Statement: Need measurable reliability/latency and test gates to maintain quality.
- Success Metrics / KPIs: observability signals per OBSERVABILITY_SPEC; test coverage targets hit (engine ≥90%, backend 85–90%, frontend 70–80%); readiness success ≥99% in normal ops; CI pass rates tracked.
- Scope In: metrics/logs/traces for start/move/quit/inference; health/readiness; load/perf baselines; quality gates.
- Scope Out: full production SRE runbooks beyond MVP.
- Constraints: follow NFRs for latency/reliability; align with TEST_STRATEGY/OBSERVABILITY_SPEC; CI gates enforced.
- Parent Epic(s): EPIC-001 (runtime observability/quality); EPIC-002 (training metrics as needed).
- Linked Requirements: NFRs for performance/observability/reliability; FRs/USs that drive instrumentation and tests.
