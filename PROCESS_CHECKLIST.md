# PROCESS_CHECKLIST.md — Governance Workflow (AGENT_CONTRACT v1.4)

In case of conflict between this checklist and AGENT_CONTRACT.md, the Contract takes precedence. This is a high-level workflow gate companion; keep AGENT_CONTRACT.md unchanged. ADR format is `ADR-NNNN-kebab-case-title.md` (Contract §0.2).

## 0) Pre-Flight / Context Recovery (Contract §0.5, §19)
- On startup/restart, read: PROJECT_POLICY.yaml, ADRs, CODE_MAP.md, docs/project_history/EPIC_LOG.md, Issues/PRs, git tags.
- Create CODE_MAP.md once structure exists; update after ≥3 module/file changes, major refactors, and at Epic reviews.
- Maintain EPIC_LOG.md at Epic start/finish (scope, key changes, ADRs).

## 1) Interview → Policy/Governance (Contract §2, §6)
- Confirm AGENT_CONTRACT v1.4; gather signals; fill PROJECT_POLICY.yaml (supervision_mode/window, workflow_profile, tier, repo_strategy, security_profile, cost guardrails, tech stack constraints, environments, domain toggles).
- Cost guardrails: cost-incurring decisions (paid services, billable infra, exceeding free tiers) need explicit supervisor approval (Contract §0.3).
- Record ADR-0001 (workflow_profile/tier/supervision/repo strategy); note ADR format.
- Capture vision, users, flows, constraints; note ambiguity tier and Proposal Branch policy availability (Contract §4.4).

## 2) Analysis & Profiling (Contract §4.1)
- Derive risk_level, size_profile, criticality; verify workflow_profile/tier fit.
- Classify system type; decide initial stack/runtime shape → ADR (tech stack/architecture).

## 3) Design (Contract §3, §5)
- Produce/refresh: VISION, REQUIREMENTS (F/NF), USER_STORIES (acceptance), ARCHITECTURE, DATA_MODEL, API_SPEC, TEST_STRATEGY, OBSERVABILITY_SPEC, SECURITY_NOTES/THREAT_MODEL (if high-risk/regulated or touching auth/PII/external integrations), DEPLOYMENT, CONFIGURATION/.env.example as soon as env/configs are introduced.
- Cross-check design/architecture against reference standards (OWASP Top 10/ASVS for web exposure, 12-Factor for services, SOLID/clean architecture for OO code); add a note in ARCHITECTURE or SECURITY docs on how major OWASP risks and 12-Factor principles are addressed when modifying services.
- Digital minimalism (Contract §5.2): justify new deps only if >200 LOC to replace, active, de facto or complex domain; avoid micro-utilities (<50 LOC) and unnecessary heavy frameworks.
- Record major design decisions as ADRs (data store, auth, integrations, cost-impact, security posture).
- Design exit gate: architecture/API/obs/test/security docs must be actionable—identify modules/components, primary flows, error/status handling, determinism, inputs/outputs, and observability hooks so that tasks can enumerate concrete files/tests later. If docs are too high-level to derive task steps, stay in Design.

## 4) Planning (Contract §6)
- Build backlog: Epics → Features → Tasks/Bugs with acceptance criteria linked to requirements/ADRs.
- Configure project board (Backlog/Ready/In Progress/In Review/Ready for Human Review/Done).
- Tag scheme: tag Epic start `epic-<id>-start`; plan feature checkpoint tags `epic-<id>-feature-<name>-done`; Epic completion `epic-<id>-complete`.
- Repo hygiene: README/CONTRIBUTING; CODE_MAP.md once code structure spans more than a trivial stub; baseline configs `.editorconfig`, formatter/linter configs, and `pre-commit` hooks covering format, lint, secrets, and basic dependency/security scans.
- CI/CD per tier and aligned to the Quality Gates Matrix: lint/format, tests, coverage gates (guard against >2pp coverage drop on affected components unless justified), security scans (deps/secrets/SAST), build.
- Templates: Issue/PR templates include ADR check and Critic Pass reminder.
- Ensure branch protection and PR-based workflow; self-merge only when Pinky Swear conditions met (Contract §15.1).
- Planning exit gate (execution-ready backlog): each Task must include 4–7 concrete steps and a Definition of Done covering implementation, required tests (with coverage targets per component), observability/logging updates, docs/ADR updates, CI/config changes, dependencies, and risk notes. Add an Execution Plan per Epic (critical path, parallelizable items, prerequisites, mapping to CI scripts/observability). Do not advance to Setup/Implementation until a Critic Pass confirms the backlog meets this bar.

## 5) Setup / Repo Hygiene (Contract §5, §15)
- Scaffold baseline files/configs: `.editorconfig`, formatter and linter configs, `pre-commit` with format/lint/secrets/dependency checks.
- Ensure CI pipelines run lint/format, unit tests, type checks, security scans, and enforce coverage thresholds from the Quality Gates Matrix.
- Verify CODE_MAP.md exists once structure is non-trivial; update if initial scaffolding added modules.
- Confirm branch protection and required checks are enabled per CI setup.

## 6) Implementation (per Task/Feature loop) (Contract §9, §15.1)
- Quality Gate: classify Task risk_level + tier (quick_fix/standard/strategic) → apply Quality Gates Matrix; ensure required tests/coverage/security/observability are satisfied and cite the applied gate in the PR.
- Understand → Plan (3–7 steps incl. tests/obs/security/risks/ambiguity tier and gate expectations) → Implement (respect architecture; update CODE_MAP on structural change) → Test (unit/API/integration/E2E per gate; determinism; avoid >2pp coverage drop on affected components unless justified) → Static checks.
- Docs & logging: docstrings and public API docs added/updated for all non-trivial modules touched; logging follows structured logging and no-secrets rules with correlation/trace IDs when available.
- Observability: primary impacted operation identified; metrics/logs/traces updated or added for that operation; SLO/SLI docs reviewed and updated if needed.
- Pattern Playbooks: does this Task match a Pattern Playbook? If yes, complete all required steps and reference the pattern name in the PR.
- Self-Review (Contract §9.6): scan for bugs, edge cases, ADR alignment before Critic Pass.
- Critic Pass completed according to the Critic Pass Procedure (perspective flip, failure scenarios/tests, red-flag escalation); note completion in PR/Issue.
- Ambiguity handling: apply 3-tier model (self-resolve; propose options; stop/seek approval) and log decisions.
- CI/repo hygiene: pre-commit hooks added/updated if needed; CI pipeline updated if new quality requirements are introduced; all required CI jobs passing for this PR.
- Summarize: update Issue/board; add feature checkpoint tags for major Features.

## 7) Maintenance/Refactor (Contract §12)
- Classify refactor (local/medium/major); ADR for medium/major with scope/risks/rollback.
- Track tech debt Issues with severity; unresolved HIGH debt needs explicit supervisor acceptance to close an Epic.

## 8) Release / Epic Review (Contract §16.2, §17, §19)
- Epic Review Bundle is tiered:
  - Minimal: completion summary; features/tasks traceability; architecture integrity check.
  - Standard: above + security/compliance; observability; testing/coverage; CI/CD status.
  - Enterprise: above + deployment readiness; risks/limitations/follow-ups; ADR index.
- Update EPIC_LOG.md; apply tags `epic-<id>-feature-<name>-done` (as used) and `epic-<id>-complete`.
- Epic-level metrics collected (Blockers, CI failures per PR before passing, post-merge regressions, coverage trends) and at least one process improvement added to EPIC_LOG.md.

## 9) Incident / Recovery (Contract §16)
- Circuit breaker: max 5 CI attempts; stop if 3 consecutive similar failures. Open Blocker Issue; revert to safe point (pre-Task commit or Epic checkpoint); pause risky work.
- Timeout: wait up to supervisor_response_window_hours; while waiting, Proposal Branch exploration allowed for alternative approach.
- Blockers: if Epic has ≥3 active Blockers, mark Epic “at risk” and summarize pattern.
- Data-state awareness (Contract §16.3): assess migrations (additive vs destructive), event logs (compensation), external APIs (reversal calls), distributed state (caches/queues/replicas). Never rollback if corruption risk; escalate complex cases.
- For incidents: create Incident/RCA; consider rollback with data-state awareness; escalate high-risk/regulated issues.

## 10) Ambiguity & Approval Management (Contract §4.4, §10, §11)
- Scope/profile/tier/requirements changes: stop impacted work; draft options (minimal/recommended/ambitious); ADR + supervisor approval; default to conservative option until confirmed.
- Cost-incurring changes require explicit approval.
- Proposal Branch policy (Contract §4.4): naming `proposal/<decision-id>-<desc>`; mark PRs `[PROPOSAL]`; max 3 active; rebase at least weekly; close/mark stale after 1.5× response window; use when awaiting high-risk approvals (tier changes, architecture changes, Tier 3 ambiguities).

## Non-Negotiable Reminders (Contract §1.2)
- Do not bypass/falsify tests, coverage, or security results.
- Do not change workflow_profile, tier, repo_strategy without ADR + approval.
- Do not introduce cost-incurring resources without approval.
- Contract takes precedence over this checklist.

## Changelog
- Added Quality Gates Matrix application, Critic Pass Procedure reference, and Pattern Playbook checks to Implementation flow.
- Added repo hygiene/CI expectations, structured logging/docstring requirements, observability tasks, and SLO review steps.
- Added Epic-level metrics and continuous-improvement prompts for EPIC_LOG.md updates.
