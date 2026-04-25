# Documentation Agent Guide

## Purpose
Use this guide for changes under `docs/`. The root `AGENTS.md` still applies; this file covers documentation trust order, lifecycle, and verification.

## Local Source Truth
- `README.md` is the canonical docs entrypoint and trust-order guide.
- `CURRENT_STATE.md` is the active implementation snapshot, but source and tests win when they disagree.
- `DEMO_PATH.md`, `API_SPEC.md`, `DEPLOYMENT.md`, `OBSERVABILITY_SPEC.md`, and `RUNBOOKS.md` describe active runtime and operational behavior.
- `ml/`, `operations/`, and `portfolio/` contain active thematic docs.
- `history/`, `history/governance/`, and ADRs are historical or contextual unless the task specifically concerns governance or project history.

## Editing Guidance
- Verify behavior claims against code, tests, configs, Dockerfiles, or package manifests before making docs sound current.
- Preserve historical docs as historical. Prefer adding correction notes or active-doc updates over rewriting archived planning context.
- Use the two-layer status model from `docs/README.md`: doc status (`Reviewed`, `Needs evidence`, `Historical`) plus capability status (`Implemented`, `Partial`, `Planned`, `Historical`).
- Keep docs navigation coherent through `docs/README.md`; do not create orphan docs.
- Keep docs concise and operational; avoid duplicating source code details that will drift quickly.

## Focused Checks
- For docs-only navigation or wording changes, use `git diff --stat`, targeted `rg`, and manual markdown review.
- Search for stale claims when moving or reclassifying docs.
- Run backend/frontend tests only when docs edits accompany behavior changes or make new behavioral claims that need verification.

## Docs Triggers
- Update `CURRENT_STATE.md` when a verified runtime, frontend, training, deployment, or testing fact changes.
- Update root `CODE_MAP.md` when subsystem boundaries, entrypoints, or command surfaces change.
- Update `DEMO_PATH.md` when setup, compose, ports, smoke commands, or demo caveats change.
- Update `API_SPEC.md` when backend route contracts change.

## Pitfalls
- Do not trust older planning docs over source.
- Do not treat generated diagnostics, screenshots, coverage, or artifact files as canonical documentation evidence.
- Do not remove caveats about simulated training orchestration unless implementation has changed.
