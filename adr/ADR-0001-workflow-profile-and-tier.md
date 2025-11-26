# ADR-0001-workflow-profile-and-tier

- Status: Accepted
- Date: 2025-11-26
- Deciders: Supervisor, Codex

## Context
- Build a production-ready Battleship web app where everyday users anonymously play against a pre-trained RL agent; MVP flows: land on homepage, start game, play, quit.
- Local-first development with future Kubernetes deployment; environments: dev, test, prod, and a separate training environment; monorepo preferred.
- Anonymous MVP (no auth/leaderboards yet); consumer data with no regulated constraints; rigorous testing, observability, and load testing desired.
- Cost guardrails: no paid SaaS or cloud resources until deployment is greenlit; open-source/self-hosted within k8s acceptable later.
- RL model lifecycle: offline training until satisfactory, then static model deployed; should support CPU/GPU training.

## Decision
- risk_level: medium (consumer app with RL opponent, non-regulated data).
- size_profile: product (single cohesive web app plus RL agent).
- criticality: normal (user-facing entertainment, not safety-critical).
- workflow_profile: standard.
- tier: standard.
- repo_strategy: monorepo (single web + RL codebase).
- supervision_mode: async; supervisor_response_window_hours: 168.

## Consequences
- Documentation: follow standard set (VISION, REQUIREMENTS, USER_STORIES, ARCHITECTURE, DATA_MODEL, API_SPEC if/when APIs formalized, TEST_STRATEGY, OBSERVABILITY_SPEC, SECURITY_NOTES/THREAT_MODEL as needed, CONFIGURATION, DEPLOYMENT, RUNBOOKS, CHANGELOG, CODE_MAP updates).
- Testing: target high coverage (90%+ for critical logic like game rules/agent integration, 85–90% general backend, 70–80% UI); include load testing for gameplay endpoints; deterministic tests where feasible.
- Security: baseline posture with secrets scanning and dependency scanning plus SAST where available; enforce least privilege and safe defaults.
- Observability: instrument gameplay and agent inference paths with metrics/logs/traces; define SLIs/SLOs for key actions (e.g., move latency).
- CI/CD: standard pipeline with lint/format, tests, coverage gating, and security checks; branch protection and PR-based changes; ensure Kubernetes compatibility even while running locally.
- Environments: keep training isolated from dev/test/prod runtimes; deploy static trained model into runtime environments; plan for local-only hosting until cloud deployment is approved.
- Cost guardrails: avoid paid services; prefer open-source components that run locally or within k8s; apply digital minimalism to dependencies.
- Domain toggles: external DB allowed when persistence is added later; auth remains simple/disabled for MVP to keep flows anonymous.
