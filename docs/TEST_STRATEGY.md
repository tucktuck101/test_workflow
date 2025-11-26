# Test Strategy (Standard Tier)

## Coverage Targets
- Game rules/engine, RL integration: ≥90% line/branch where practical.
- Backend APIs/services: 85–90%.
- Frontend UI/presentation: 70–80%.
- Exclusions: none planned; any future exclusion must be justified here and in code.

## Test Types
- Unit: board/rule validation, move handling, RL inference wrapper (stubbed), health checks.
- API/contract: start/move/quit flows; invalid/duplicate/out-of-bounds moves; finished-game requests rejected.
- Integration: agent inference invoked within turn handling; model load paths; in-memory state lifecycle.
- Frontend: component and flow tests for start/play/quit; error/display states.
- Load: move endpoint and game start under concurrent users (e.g., k6 or Locust), targeting low-latency turns.
- Smoke: startup, health endpoints, model load.

## Determinism
- RL inference uses deterministic mode with fixed seed for tests; if unavailable, substitute stub/fake agent with predictable policy.
- Unit/API/integration tests must not rely on randomness; seed per test module.
- Load tests isolated from unit/CI runs; gated to avoid flaky results.

## Quality Gate Alignment (risk: medium, tier: standard)
- Required in CI: lint/format, unit tests (engine + inference adapter), API/contract tests for start/move/quit (including 400/404/409/503 cases), type checks (mypy/ts), coverage thresholds per targets above (CI threshold ≥85% overall, tighter per-component targets enforced by suites), and dependency/secrets scans.
- Not required in every CI run but planned: load tests (manual/nightly), property-based tests for move validation, GPU-path smoke when available.
- Coverage guardrail: no >2pp drop on touched components without explicit justification in PR; new code should bring coverage up to target band.

## Flake Prevention
- Enforce deterministic seeds for board generation and agent stubs; isolate RNG per test.
- Avoid network/external calls in unit/API tests; stub model load where appropriate.
- Keep load/perf tests separate from main CI; run under controlled environments only.

## Tooling (proposed)
- Backend: pytest + hypothesis optional, requests/httpx for API tests; fixtures for seeded boards and stubbed agent.
- Frontend: vitest/react-testing-library (if Vite/React).
- Load: k6 or Locust (scripted; optional in CI depending on time budget; run manually or in a nightly job).

## Security Checks
- Dependency scanning and secrets scanning in CI; basic SAST where available for Python/TypeScript.

## Gating and Execution
- CI: run unit + API-level tests, lint, type checks; keep deterministic and fast.
- Manual/periodic: load tests and longer-running property-based suites; record results and thresholds.
- Coverage: fail CI if coverage drops by >2pp on touched components unless justified.
